"""Domain-Specific Finding, Evidence, Reproduction, RootCause, and Report Repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.db.models import (
    EvidenceModel,
    FindingModel,
    ReportModel,
    ReproductionAttemptModel,
    RootCauseModel,
)
from packages.domain.models import (
    ArtifactReference,
    Evidence,
    EvidenceType,
    Finding,
    FindingCategory,
    FindingSeverity,
    HypothesisType,
    Provenance,
    Report,
    ReproductionAttempt,
    ReproductionStatus,
    RootCause,
    VerificationStatus,
)


class FindingRepository:
    """Thin repository handling Findings, Evidence, Multi-Attempt Reproductions, Root Causes, and Reports."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _finding_to_domain(self, model: FindingModel) -> Finding:
        """Convert FindingModel and its loaded children to domain Finding entity."""
        repros = [
            ReproductionAttempt(
                id=r.id,
                finding_id=r.finding_id,
                session_id=r.session_id,
                attempt_number=r.attempt_number,
                framework=r.framework,
                script_code=r.script_code,
                status=ReproductionStatus(r.status),
                execution_output=r.execution_output,
                duration_ms=r.duration_ms,
                artifacts=[ArtifactReference.model_validate(a) for a in r.artifacts],
                started_at=r.started_at,
                completed_at=r.completed_at,
            )
            for r in (model.reproductions or [])
        ]
        rcs = [
            RootCause(
                id=rc.id,
                finding_id=rc.finding_id,
                session_id=rc.session_id,
                hypothesis_type=HypothesisType(rc.hypothesis_type),
                commit_hash=rc.commit_hash,
                file_path=rc.file_path,
                line_number=rc.line_number,
                diff_chunk=rc.diff_chunk,
                explanation=rc.explanation,
                confidence=rc.confidence,
                affected_components=rc.affected_components or [],
                supporting_evidence_ids=[
                    uuid.UUID(str(eid)) for eid in (rc.supporting_evidence_ids or [])
                ],
                created_at=rc.created_at,
            )
            for rc in (model.root_causes or [])
        ]
        ev_ids = [uuid.UUID(str(eid)) for eid in (model.evidence_ids or [])]

        return Finding(
            id=model.id,
            session_id=model.session_id,
            category=FindingCategory(model.category),
            severity=FindingSeverity(model.severity),
            title=model.title,
            description=model.description,
            workflow_path=model.workflow_path or [],
            confidence=model.confidence,
            status=VerificationStatus(model.status),
            evidence_ids=ev_ids,
            reproductions=repros,
            root_causes=rcs,
            created_at=model.created_at,
        )

    async def create_finding(self, finding: Finding) -> Finding:
        """Create and persist a new Finding."""
        ev_ids_json = [str(eid) for eid in finding.evidence_ids]
        model = FindingModel(
            id=finding.id,
            session_id=finding.session_id,
            category=finding.category.value,
            severity=finding.severity.value,
            title=finding.title,
            description=finding.description,
            workflow_path=finding.workflow_path,
            confidence=finding.confidence,
            status=finding.status.value,
            evidence_ids=ev_ids_json,
        )
        self.session.add(model)
        await self.session.flush()
        return finding

    async def get_finding(self, finding_id: uuid.UUID) -> Finding | None:
        """Retrieve a Finding with its reproduction attempts and root causes."""
        stmt = (
            select(FindingModel)
            .where(FindingModel.id == finding_id)
            .options(
                selectinload(FindingModel.reproductions),
                selectinload(FindingModel.root_causes),
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._finding_to_domain(model) if model else None

    async def list_findings_by_session(self, session_id: uuid.UUID) -> list[Finding]:
        """List all findings for an analysis session."""
        stmt = (
            select(FindingModel)
            .where(FindingModel.session_id == session_id)
            .options(
                selectinload(FindingModel.reproductions),
                selectinload(FindingModel.root_causes),
            )
            .order_by(FindingModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._finding_to_domain(m) for m in models]

    async def update_finding_status(
        self, finding_id: uuid.UUID, new_status: VerificationStatus
    ) -> Finding | None:
        """Update finding verification status."""
        stmt = (
            update(FindingModel)
            .where(FindingModel.id == finding_id)
            .values(status=new_status.value, updated_at=datetime.now(UTC))
            .returning(FindingModel)
        )
        result = await self.session.execute(stmt)
        updated = result.scalar_one_or_none()
        if not updated:
            return None
        return await self.get_finding(finding_id)

    async def record_evidence(self, evidence: Evidence) -> Evidence:
        """Persist a piece of deterministic evidence with provenance and artifact references."""
        artifacts_json = [a.model_dump(mode="json") for a in evidence.artifacts]
        provenance_json = evidence.provenance.model_dump(mode="json")

        model = EvidenceModel(
            id=evidence.id,
            session_id=evidence.session_id,
            version_id=evidence.version_id,
            trajectory_id=evidence.trajectory_id,
            observation_id=evidence.observation_id,
            finding_id=evidence.finding_id,
            evidence_type=evidence.evidence_type.value,
            description=evidence.description,
            payload=evidence.payload,
            artifacts=artifacts_json,
            provenance=provenance_json,
            collected_at=evidence.collected_at,
        )
        self.session.add(model)
        await self.session.flush()
        return evidence

    async def list_evidence_by_session(self, session_id: uuid.UUID) -> list[Evidence]:
        """List all evidence captured during an analysis session."""
        stmt = (
            select(EvidenceModel)
            .where(EvidenceModel.session_id == session_id)
            .order_by(EvidenceModel.collected_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            Evidence(
                id=m.id,
                session_id=m.session_id,
                version_id=m.version_id,
                trajectory_id=m.trajectory_id,
                observation_id=m.observation_id,
                finding_id=m.finding_id,
                evidence_type=EvidenceType(m.evidence_type),
                description=m.description,
                payload=m.payload,
                artifacts=[ArtifactReference.model_validate(a) for a in m.artifacts],
                provenance=Provenance.model_validate(m.provenance),
                collected_at=m.collected_at,
            )
            for m in models
        ]

    async def record_reproduction_attempt(
        self, attempt: ReproductionAttempt
    ) -> ReproductionAttempt:
        """Record an autonomous reproduction attempt for a finding."""
        artifacts_json = [a.model_dump(mode="json") for a in attempt.artifacts]
        model = ReproductionAttemptModel(
            id=attempt.id,
            finding_id=attempt.finding_id,
            session_id=attempt.session_id,
            attempt_number=attempt.attempt_number,
            framework=attempt.framework,
            script_code=attempt.script_code,
            status=attempt.status.value,
            execution_output=attempt.execution_output,
            duration_ms=attempt.duration_ms,
            artifacts=artifacts_json,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
        )
        self.session.add(model)
        await self.session.flush()
        return attempt

    async def list_reproductions_by_finding(
        self, finding_id: uuid.UUID
    ) -> list[ReproductionAttempt]:
        """List all reproduction attempts for a finding ordered by attempt number."""
        stmt = (
            select(ReproductionAttemptModel)
            .where(ReproductionAttemptModel.finding_id == finding_id)
            .order_by(ReproductionAttemptModel.attempt_number.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            ReproductionAttempt(
                id=m.id,
                finding_id=m.finding_id,
                session_id=m.session_id,
                attempt_number=m.attempt_number,
                framework=m.framework,
                script_code=m.script_code,
                status=ReproductionStatus(m.status),
                execution_output=m.execution_output,
                duration_ms=m.duration_ms,
                artifacts=[ArtifactReference.model_validate(a) for a in m.artifacts],
                started_at=m.started_at,
                completed_at=m.completed_at,
            )
            for m in models
        ]

    async def record_root_cause(self, root_cause: RootCause) -> RootCause:
        """Record a correlated root cause hypothesis or observed fact."""
        ev_ids_json = [str(eid) for eid in root_cause.supporting_evidence_ids]
        model = RootCauseModel(
            id=root_cause.id,
            finding_id=root_cause.finding_id,
            session_id=root_cause.session_id,
            hypothesis_type=root_cause.hypothesis_type.value,
            commit_hash=root_cause.commit_hash,
            file_path=root_cause.file_path,
            line_number=root_cause.line_number,
            diff_chunk=root_cause.diff_chunk,
            explanation=root_cause.explanation,
            confidence=root_cause.confidence,
            affected_components=root_cause.affected_components,
            supporting_evidence_ids=ev_ids_json,
            created_at=root_cause.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return root_cause

    async def create_or_update_report(self, report: Report) -> Report:
        """Persist a derived engineering report for an analysis session."""
        stats_json = {
            "total_workflows": report.total_workflows,
            "verified_regressions": report.verified_regressions,
            "false_positives_filtered": report.false_positives_filtered,
            "duration_seconds": report.duration_seconds,
        }
        stmt = select(ReportModel).where(ReportModel.session_id == report.session_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.summary = report.summary
            existing.stats = stats_json
            existing.metadata_json = report.metadata
            existing.generated_at = report.generated_at
            await self.session.flush()
        else:
            model = ReportModel(
                id=report.id,
                session_id=report.session_id,
                summary=report.summary,
                stats=stats_json,
                generated_at=report.generated_at,
                metadata_json=report.metadata,
            )
            self.session.add(model)
            await self.session.flush()

        return report

    async def get_report_by_session(self, session_id: uuid.UUID) -> Report | None:
        """Retrieve synthesized report for an analysis session."""
        stmt = select(ReportModel).where(ReportModel.session_id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        findings = await self.list_findings_by_session(session_id)
        stats = model.stats or {}

        return Report(
            id=model.id,
            session_id=model.session_id,
            summary=model.summary,
            findings=findings,
            total_workflows=stats.get("total_workflows", 0),
            verified_regressions=stats.get("verified_regressions", 0),
            false_positives_filtered=stats.get("false_positives_filtered", 0),
            duration_seconds=stats.get("duration_seconds", 0.0),
            generated_at=model.generated_at,
            metadata=model.metadata_json or {},
        )
