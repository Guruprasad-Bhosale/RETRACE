"""Accessibility Semantic Difference Analyzer.

Extracts deterministic differences in accessibility tree structures, roles, names,
and state properties without fabricating unsubstantiated nodes.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    AccessibilityDifference,
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class AccessibilityDiffer:
    """Compares observable accessibility tree signatures and role/name mappings."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[AccessibilityDifference]:
        """Extract deterministic accessibility differences from an AlignmentResult."""
        if not self.config.enable_a11y_diff:
            return []

        differences: list[AccessibilityDifference] = []
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
            canonical_subj = f"a11y:{route}"

            # Structural A11y Signature Divergence
            a11y_a = sig_a.a11y_signature
            a11y_b = sig_b.a11y_signature
            if a11y_a and a11y_b and a11y_a != a11y_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ACCESSIBILITY,
                    kind=DifferenceKind.A11Y_STRUCTURE_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=a11y_a,
                    after_identity=a11y_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=a11y_a,
                    after_value=a11y_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={"a11y_signature_a": a11y_a, "a11y_signature_b": a11y_b, "route": route},
                    comparison_completeness="signature_level",
                )
                differences.append(
                    AccessibilityDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ACCESSIBILITY,
                        kind=DifferenceKind.A11Y_STRUCTURE_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Accessibility tree structure changed at route '{route}'."
                        ),
                        evidence=[evidence],
                    )
                )

        return differences
