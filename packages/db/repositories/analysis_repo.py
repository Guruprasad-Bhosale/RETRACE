"""Domain-Specific Analysis Session Repository with Optimistic Concurrency Control."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import AnalysisSessionModel
from packages.domain.models import AnalysisSession, AnalysisStatus, ApplicationVersion


class ConcurrencyError(Exception):
    """Raised when an optimistic concurrency version check fails."""

    pass


class AnalysisSessionRepository:
    """Thin repository for AnalysisSession lifecycle and metrics with optimistic locking."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_domain(self, model: AnalysisSessionModel) -> AnalysisSession:
        """Map ORM model to pure domain entity."""
        v_a = ApplicationVersion.model_validate(model.version_a_meta)
        v_b = ApplicationVersion.model_validate(model.version_b_meta)
        return AnalysisSession(
            id=model.id,
            project_id=model.project_id,
            version_a=v_a,
            version_b=v_b,
            status=AnalysisStatus(model.status),
            version=model.version,
            config=model.config,
            workflows_explored=model.workflows_explored,
            regressions_count=model.regressions_count,
            error_message=model.error_message,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )

    async def create_analysis_session(
        self,
        project_id: uuid.UUID,
        version_a: ApplicationVersion,
        version_b: ApplicationVersion,
        config: dict | None = None,
    ) -> AnalysisSession:
        """Create and persist a new AnalysisSession."""
        session_id = uuid.uuid4()
        model = AnalysisSessionModel(
            id=session_id,
            project_id=project_id,
            version_a_id=version_a.id,
            version_b_id=version_b.id,
            version_a_meta=version_a.model_dump(mode="json"),
            version_b_meta=version_b.model_dump(mode="json"),
            status=AnalysisStatus.PENDING.value,
            version=1,
            config=config or {},
            workflows_explored=0,
            regressions_count=0,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_analysis_session(self, session_id: uuid.UUID) -> AnalysisSession | None:
        """Retrieve an analysis session by ID."""
        stmt = select(AnalysisSessionModel).where(AnalysisSessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update_status(
        self,
        session_id: uuid.UUID,
        expected_version: int,
        new_status: AnalysisStatus,
        error_message: str | None = None,
    ) -> AnalysisSession:
        """Transition analysis status safely using optimistic concurrency control.

        Raises:
            ConcurrencyError: If the record was modified concurrently by another worker.
            ValueError: If the session does not exist.
        """
        values: dict = {
            "status": new_status.value,
            "version": AnalysisSessionModel.version + 1,
            "error_message": error_message,
        }
        if new_status == AnalysisStatus.RUNNING:
            values["started_at"] = datetime.now(UTC)
        elif new_status in (
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        ):
            values["completed_at"] = datetime.now(UTC)

        stmt = (
            update(AnalysisSessionModel)
            .where(
                AnalysisSessionModel.id == session_id,
                AnalysisSessionModel.version == expected_version,
            )
            .values(**values)
            .returning(AnalysisSessionModel)
        )
        result = await self.session.execute(stmt)
        updated_model = result.scalar_one_or_none()

        if updated_model is None:
            # Check if record exists or failed version check
            existing = await self.get_analysis_session(session_id)
            if existing is None:
                raise ValueError(f"Analysis session {session_id} not found")
            raise ConcurrencyError(
                f"Optimistic lock conflict on AnalysisSession {session_id}: "
                f"expected version {expected_version} but found version {existing.version}"
            )

        return self._to_domain(updated_model)

    async def update_metrics(
        self,
        session_id: uuid.UUID,
        workflows_explored: int | None = None,
        regressions_count: int | None = None,
    ) -> None:
        """Update explored workflows and regression counts."""
        values: dict = {}
        if workflows_explored is not None:
            values["workflows_explored"] = workflows_explored
        if regressions_count is not None:
            values["regressions_count"] = regressions_count

        if values:
            stmt = (
                update(AnalysisSessionModel)
                .where(AnalysisSessionModel.id == session_id)
                .values(**values)
            )
            await self.session.execute(stmt)

    async def list_by_project(self, project_id: uuid.UUID) -> list[AnalysisSession]:
        """List all analysis sessions for a project."""
        stmt = (
            select(AnalysisSessionModel)
            .where(AnalysisSessionModel.project_id == project_id)
            .order_by(AnalysisSessionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_recent(self, limit: int = 50) -> list[AnalysisSession]:
        """List most recent analysis sessions."""
        stmt = (
            select(AnalysisSessionModel)
            .order_by(AnalysisSessionModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]
