"""Domain-Specific Project and Application Version Repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import ApplicationVersionModel, ProjectModel
from packages.domain.models import ApplicationVersion, Project


class ProjectRepository:
    """Thin repository handling Project and ApplicationVersion persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(self, name: str, description: str | None = None) -> Project:
        """Create and persist a new Project."""
        project_id = uuid.uuid4()
        model = ProjectModel(
            id=project_id,
            name=name,
            description=description,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return Project.model_validate(model)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        """Retrieve a project by primary key ID."""
        stmt = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return Project.model_validate(model) if model else None

    async def list_projects(self) -> list[Project]:
        """List all projects ordered by creation time descending."""
        stmt = select(ProjectModel).order_by(ProjectModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Project.model_validate(m) for m in models]

    def _version_to_domain(self, model: ApplicationVersionModel) -> ApplicationVersion:
        return ApplicationVersion(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            base_url=model.base_url,
            git_repo_url=model.git_repo_url,
            git_commit_hash=model.git_commit_hash,
            branch=model.branch,
            build_id=model.build_id,
            environment_variables=model.environment_variables or {},
            metadata=model.metadata_json or {},
            created_at=model.created_at,
        )

    async def create_version(
        self,
        name: str,
        base_url: str,
        project_id: uuid.UUID | None = None,
        git_repo_url: str | None = None,
        git_commit_hash: str | None = None,
        branch: str | None = None,
        build_id: str | None = None,
        environment_variables: dict[str, str] | None = None,
        metadata: dict | None = None,
    ) -> ApplicationVersion:
        """Create and persist an ApplicationVersion entity."""
        version_id = uuid.uuid4()
        model = ApplicationVersionModel(
            id=version_id,
            project_id=project_id,
            name=name,
            base_url=base_url,
            git_repo_url=git_repo_url,
            git_commit_hash=git_commit_hash,
            branch=branch,
            build_id=build_id,
            environment_variables=environment_variables or {},
            metadata_json=metadata or {},
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._version_to_domain(model)

    async def get_version(self, version_id: uuid.UUID) -> ApplicationVersion | None:
        """Retrieve an application version by ID."""
        stmt = select(ApplicationVersionModel).where(ApplicationVersionModel.id == version_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._version_to_domain(model) if model else None

    async def list_versions_by_project(self, project_id: uuid.UUID) -> list[ApplicationVersion]:
        """List all application versions belonging to a project."""
        stmt = (
            select(ApplicationVersionModel)
            .where(ApplicationVersionModel.project_id == project_id)
            .order_by(ApplicationVersionModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._version_to_domain(m) for m in models]
