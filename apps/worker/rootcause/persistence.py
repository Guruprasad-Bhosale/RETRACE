"""Persistence and Domain Entity Mapping Layer.

Transforms RootCauseResult domain models into Phase 1 RootCause, Evidence,
and SQLAlchemy ORM models for structured database persistence.
"""

from uuid import UUID, uuid4

from apps.worker.rootcause.models import RootCauseAttribution, RootCauseResult
from packages.db.models import EvidenceModel, RootCauseModel
from packages.domain.models import (
    Evidence,
    EvidenceType,
    HypothesisType,
    Provenance,
    RootCause,
)


class RootCausePersistenceMapper:
    """Mapper between worker root-cause results and persisted domain/database entities."""

    @classmethod
    def to_domain_root_cause(
        cls,
        result: RootCauseResult,
        finding_id: UUID,
        session_id: UUID,
    ) -> RootCause | None:
        """Convert RootCauseResult primary attribution into a domain RootCause entity."""
        if not result.primary_attribution:
            return None

        attr = result.primary_attribution
        loc = attr.source_location
        commit_h = attr.commit.commit_hash if attr.commit else loc.commit_hash

        diff_chunk_str: str | None = None
        if attr.diff_hunk:
            diff_chunk_str = "\n".join(dl.content for dl in attr.diff_hunk.lines)

        hypo_type = (
            HypothesisType.OBSERVED_FACT
            if result.status.value == "LOCATED"
            else HypothesisType.HYPOTHESIS
        )

        affected = [loc.file_path]
        if loc.symbol_name:
            affected.append(loc.symbol_name)

        return RootCause(
            id=uuid4(),
            finding_id=finding_id,
            session_id=session_id,
            hypothesis_type=hypo_type,
            commit_hash=commit_h,
            file_path=loc.file_path,
            line_number=loc.start_line,
            diff_chunk=diff_chunk_str,
            explanation=attr.explanation,
            confidence=1.0 if result.status.value == "LOCATED" else 0.5,
            affected_components=affected,
            supporting_evidence_ids=[],
        )

    @classmethod
    def to_domain_evidence(
        cls,
        attribution: RootCauseAttribution,
        session_id: UUID,
        finding_id: UUID | None = None,
        version_id: UUID | None = None,
    ) -> Evidence:
        """Convert a single RootCauseAttribution into a domain Evidence entity."""
        loc = attribution.source_location
        diff_payload = {
            "file_path": loc.file_path,
            "start_line": loc.start_line,
            "end_line": loc.end_line,
            "symbol_name": loc.symbol_name,
            "symbol_kind": loc.symbol_kind.value if loc.symbol_kind else None,
            "relationship_type": attribution.relationship_type.value,
            "commit_attribution_type": attribution.commit_attribution_type.value,
            "commit_hash": attribution.commit.commit_hash if attribution.commit else None,
        }

        prov = Provenance(
            analysis_id=session_id,
            version_id=version_id or uuid4(),
            step_index=0,
            collector_service="root-cause-localization-engine",
            environment_context={"repository_path": loc.repository_path},
            metadata={"attribution_id": attribution.attribution_id},
        )

        return Evidence(
            id=uuid4(),
            session_id=session_id,
            version_id=version_id,
            finding_id=finding_id,
            evidence_type=EvidenceType.GIT_DIFF,
            description=attribution.explanation,
            payload=diff_payload,
            artifacts=[],
            provenance=prov,
        )

    @classmethod
    def to_orm_root_cause(
        cls,
        root_cause: RootCause,
    ) -> RootCauseModel:
        """Convert a domain RootCause entity to an ORM RootCauseModel."""
        return RootCauseModel(
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
            supporting_evidence_ids=[str(i) for i in root_cause.supporting_evidence_ids],
            created_at=root_cause.created_at,
        )

    @classmethod
    def to_orm_evidence(
        cls,
        evidence: Evidence,
    ) -> EvidenceModel:
        """Convert a domain Evidence entity to an ORM EvidenceModel."""
        return EvidenceModel(
            id=evidence.id,
            session_id=evidence.session_id,
            version_id=evidence.version_id,
            trajectory_id=evidence.trajectory_id,
            observation_id=evidence.observation_id,
            finding_id=evidence.finding_id,
            evidence_type=evidence.evidence_type.value,
            description=evidence.description,
            payload=evidence.payload,
            artifacts=[a.model_dump(mode="json") for a in evidence.artifacts],
            provenance=evidence.provenance.model_dump(mode="json"),
            collected_at=evidence.collected_at,
        )
