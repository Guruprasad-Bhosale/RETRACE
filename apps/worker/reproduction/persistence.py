"""Reproduction Persistence Mapper for Core Domain Entities."""

import json
from uuid import UUID

from apps.worker.reproduction.models import (
    ReproductionAttemptResult,
)
from apps.worker.reproduction.models import (
    ReproductionStatus as EngineReproStatus,
)
from packages.domain.models import (
    ReproductionAttempt as DomainReproductionAttempt,
)
from packages.domain.models import (
    ReproductionStatus as DomainReproStatus,
)


class ReproductionPersistenceMapper:
    """Transforms Phase 8 ReproductionAttemptResults into authoritative Phase 1 domain ReproductionAttempt models."""

    @staticmethod
    def map_status_to_domain(status: EngineReproStatus) -> DomainReproStatus:
        """Map internal Phase 8 reproduction status to Phase 1 domain ReproductionStatus enum."""
        mapping = {
            EngineReproStatus.REPRODUCED: DomainReproStatus.SUCCEEDED,
            EngineReproStatus.NOT_REPRODUCED: DomainReproStatus.FAILED,
            EngineReproStatus.INCONCLUSIVE: DomainReproStatus.FAILED,
            EngineReproStatus.FAILED: DomainReproStatus.ERROR,
            EngineReproStatus.BLOCKED: DomainReproStatus.SKIPPED,
            EngineReproStatus.PLANNED: DomainReproStatus.SKIPPED,
            EngineReproStatus.RUNNING: DomainReproStatus.SKIPPED,
        }
        return mapping.get(status, DomainReproStatus.FAILED)

    @classmethod
    def to_domain_attempt(
        cls,
        attempt: ReproductionAttemptResult,
        finding_id: UUID,
        session_id: UUID,
        path_summary: dict | None = None,
    ) -> DomainReproductionAttempt:
        """Convert a single attempt result into a Phase 1 ReproductionAttempt domain entity."""
        domain_status = cls.map_status_to_domain(attempt.status)

        output_summary = {
            "strategy": attempt.strategy.value,
            "status": attempt.status.value,
            "verification": attempt.verification.model_dump() if attempt.verification else None,
            "failure_reason": attempt.failure_reason,
            "observations_a_count": len(attempt.evidence.observations_a),
            "observations_b_count": len(attempt.evidence.observations_b),
        }

        # Store structured replay path specification in script_code metadata field
        structured_spec = {
            "attempt_id": str(attempt.attempt_id),
            "path": path_summary or {},
        }

        return DomainReproductionAttempt(
            id=attempt.attempt_id,
            finding_id=finding_id,
            session_id=session_id,
            attempt_number=attempt.attempt_number,
            framework="playwright_python",
            script_code=json.dumps(structured_spec, indent=2),
            status=domain_status,
            execution_output=json.dumps(output_summary, indent=2),
            duration_ms=attempt.duration_ms,
            artifacts=list(attempt.evidence.artifact_references),
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
        )
