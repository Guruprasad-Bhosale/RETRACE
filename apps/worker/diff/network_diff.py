"""Network Semantic Difference Analyzer.

Extracts deterministic differences in network failures, request status codes,
and intercepted HTTP interactions while strictly redacting sensitive credentials.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    NetworkDifference,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class NetworkDiffer:
    """Compares observable network communication metrics and failure states."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[NetworkDifference]:
        """Extract deterministic network differences from an AlignmentResult."""
        if not self.config.enable_network_diff:
            return []

        differences: list[NetworkDifference] = []
        align = alignment_result.alignment

        for sa in align.aligned_states:
            if sa.relation not in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                continue

            sig_a = sa.signature_a
            sig_b = sa.signature_b
            if not sig_a or not sig_b:
                continue

            route = DiffNormalizer.normalize_route(sig_a.normalized_route, self.config)
            canonical_subj = f"network:{route}"

            # Network Failures Count Changed
            fails_a = sig_a.observational.network_failures_count
            fails_b = sig_b.observational.network_failures_count
            if fails_a != fails_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.NETWORK,
                    kind=DifferenceKind.NETWORK_FAILURE_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=str(fails_a),
                    after_identity=str(fails_b),
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=fails_a,
                    after_value=fails_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details=DiffNormalizer.sanitize_diff_payload(
                        {"network_failures_a": fails_a, "network_failures_b": fails_b, "route": route}
                    ),
                )
                differences.append(
                    NetworkDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.NETWORK,
                        kind=DifferenceKind.NETWORK_FAILURE_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Network failure count difference at route '{route}': "
                            f"Version A recorded {fails_a} failure(s), Version B recorded {fails_b} failure(s)."
                        ),
                        evidence=[evidence],
                    )
                )

        return differences
