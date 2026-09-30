"""Artifact Management and Observation Transformation for Reproduction Runs."""

from uuid import UUID

from apps.worker.reproduction.models import ReproductionObservation
from packages.domain.models import Observation


class ReproductionArtifactMapper:
    """Transforms Phase 3 domain Observations into typed ReproductionObservations."""

    @staticmethod
    def from_domain_observation(
        obs: Observation,
        version_id: UUID,
        duration_ms: float = 0.0,
        action_success: bool = True,
        error_message: str | None = None,
    ) -> ReproductionObservation:
        """Map a Phase 3 Observation into a ReproductionObservation."""
        state = obs.state
        return ReproductionObservation(
            reproduction_observation_id=obs.id,
            version_id=version_id,
            step_index=obs.step_index,
            url=state.url,
            http_status=state.http_status,
            dom_hash=state.dom_hash,
            a11y_tree_hash=state.a11y_tree_hash,
            page_title=state.page_title,
            console_errors_count=state.console_errors_count,
            console_warnings_count=state.console_warnings_count,
            page_errors_count=state.summary.get("page_errors_count", 0) if state.summary else 0,
            network_failures_count=state.network_failures_count,
            interactive_elements_count=state.interactive_elements_count,
            duration_ms=duration_ms,
            action_success=action_success,
            error_message=error_message,
            artifact_references=list(obs.artifacts),
            metadata=dict(obs.provenance.metadata) if obs.provenance else {},
        )
