"""Performance Timing Semantic Difference Analyzer.

Extracts deterministic differences in navigation, network, and stabilization durations
while preserving raw values and units without severity judgment.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    PerformanceDifference,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class PerformanceDiffer:
    """Compares observable execution and stabilization timings neutrally."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[PerformanceDifference]:
        """Extract deterministic performance differences from an AlignmentResult."""
        if not self.config.enable_performance_diff:
            return []

        differences: list[PerformanceDifference] = []
        align = alignment_result.alignment

        for ta in align.aligned_transitions:
            if ta.relation not in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                continue

            act_align = ta.action_alignment
            if not act_align or not act_align.signature_a or not act_align.signature_b:
                continue

            sig_a = act_align.signature_a
            sig_b = act_align.signature_b

            dur_a_raw = sig_a.semantic_attributes.get("duration_ms")
            dur_b_raw = sig_b.semantic_attributes.get("duration_ms")

            if dur_a_raw is not None and dur_b_raw is not None:
                try:
                    dur_a = float(dur_a_raw)
                    dur_b = float(dur_b_raw)
                except (ValueError, TypeError):
                    continue

                delta = abs(dur_b - dur_a)
                if delta >= self.config.timing_min_observable_delta_ms:
                    dur_a_norm = DiffNormalizer.normalize_timing(dur_a)
                    dur_b_norm = DiffNormalizer.normalize_timing(dur_b)
                    canonical_subj = f"timing:{sig_a.stable_target_identity}"
                    diff_id = compute_deterministic_diff_id(
                        category=DifferenceCategory.PERFORMANCE,
                        kind=DifferenceKind.NAVIGATION_DURATION_CHANGED,
                        canonical_subject=canonical_subj,
                        before_identity=f"{dur_a_norm}ms",
                        after_identity=f"{dur_b_norm}ms",
                    )
                    evidence = DifferenceEvidence(
                        canonical_subject=canonical_subj,
                        before_value=f"{dur_a_norm} ms",
                        after_value=f"{dur_b_norm} ms",
                        action_a_id=act_align.action_a_id,
                        action_b_id=act_align.action_b_id,
                        transition_a_id=ta.transition_a_id,
                        transition_b_id=ta.transition_b_id,
                        source_state_id=ta.from_state_a_id,
                        target_state_id=ta.to_state_a_id,
                        details={
                            "duration_a_ms": dur_a_norm,
                            "duration_b_ms": dur_b_norm,
                            "delta_ms": round(dur_b_norm - dur_a_norm, 2),
                            "unit": "ms",
                        },
                    )
                    differences.append(
                        PerformanceDifference(
                            diff_id=diff_id,
                            category=DifferenceCategory.PERFORMANCE,
                            kind=DifferenceKind.NAVIGATION_DURATION_CHANGED,
                            canonical_subject=canonical_subj,
                            comparison_status=ComparisonStatus.COMPARED,
                            description=(
                                f"Observed transition duration difference for '{sig_a.stable_target_identity}': "
                                f"Version A was {dur_a_norm} ms, Version B was {dur_b_norm} ms (delta: {round(dur_b - dur_a, 2):+0.2f} ms)."
                            ),
                            evidence=[evidence],
                        )
                    )

        return differences
