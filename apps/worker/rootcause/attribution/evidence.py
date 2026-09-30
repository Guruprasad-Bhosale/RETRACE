"""Attribution Evidence Construction Layer.

Builds structured, verifiable AttributionEvidence binding behavioral observations to source diffs.
"""

from apps.worker.regression.models import RegressionClassification
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.localization.behavioral import LocalizedCandidate
from apps.worker.rootcause.models import (
    AttributionEvidence,
    CommitAttributionType,
    CommitMetadata,
)


class AttributionEvidenceBuilder:
    """Builder for immutable AttributionEvidence objects."""

    @classmethod
    def build(
        cls,
        candidate: LocalizedCandidate,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        commit: CommitMetadata | None = None,
        commit_attribution_type: CommitAttributionType = CommitAttributionType.NO_ATTRIBUTABLE_COMMIT,
    ) -> AttributionEvidence:
        """Construct structured AttributionEvidence linking behavioral and source evidence."""
        repro_obs_ids = []
        repro_id = None
        if reproduction:
            repro_id = reproduction.reproduction_id
            for attempt in reproduction.attempts:
                for obs in attempt.evidence.observations_a + attempt.evidence.observations_b:
                    repro_obs_ids.append(obs.reproduction_observation_id)

        return AttributionEvidence(
            source_location=candidate.source_location,
            relationship_type=candidate.relationship_type,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=repro_id,
            reproduction_observation_ids=repro_obs_ids,
            diff_hunk=candidate.diff_hunk,
            commit_evidence=commit,
            commit_attribution_type=commit_attribution_type,
            explanation=candidate.explanation,
            details={
                "category": classification.category.value,
                "rule_id": classification.rule_id,
                "symbol_name": candidate.symbol.name if candidate.symbol else None,
                "symbol_kind": candidate.symbol.kind.value if candidate.symbol else None,
            },
        )
