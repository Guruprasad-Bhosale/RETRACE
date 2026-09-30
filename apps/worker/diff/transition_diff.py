"""Transition Semantic Difference Analyzer.

Extracts deterministic differences across directed state transitions, target outcomes,
missing/additional transitions, and ambiguous branching.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    TransitionDifference,
    compute_deterministic_diff_id,
)


class TransitionDiffer:
    """Compares directed transitions and detects target state deviations and missing paths."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[TransitionDifference]:
        """Extract deterministic transition differences from an AlignmentResult."""
        if not self.config.enable_transition_diff:
            return []

        differences: list[TransitionDifference] = []
        align = alignment_result.alignment

        # 1. Aligned Transitions
        for ta in align.aligned_transitions:
            if ta.relation in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                to_a = ta.to_state_a_id
                to_b = ta.to_state_b_id
                from_a = ta.from_state_a_id
                from_b = ta.from_state_b_id

                # Target State Deviation: Same or matched action leads to a different target state
                if to_a and to_b and to_a != to_b:
                    canonical_subj = f"transition:{from_a}->{to_a}"
                    diff_id = compute_deterministic_diff_id(
                        category=DifferenceCategory.TRANSITION,
                        kind=DifferenceKind.TRANSITION_TARGET_CHANGED,
                        canonical_subject=canonical_subj,
                        before_identity=to_a,
                        after_identity=to_b,
                    )
                    evidence = DifferenceEvidence(
                        canonical_subject=canonical_subj,
                        before_value=to_a,
                        after_value=to_b,
                        transition_a_id=ta.transition_a_id,
                        transition_b_id=ta.transition_b_id,
                        action_a_id=ta.action_alignment.action_a_id if ta.action_alignment else None,
                        action_b_id=ta.action_alignment.action_b_id if ta.action_alignment else None,
                        source_state_id=from_a,
                        target_state_id=to_a,
                        state_a_id=from_a,
                        state_b_id=from_b,
                        details={"to_state_a": to_a, "to_state_b": to_b, "from_state_a": from_a, "from_state_b": from_b},
                    )
                    differences.append(
                        TransitionDifference(
                            diff_id=diff_id,
                            category=DifferenceCategory.TRANSITION,
                            kind=DifferenceKind.TRANSITION_TARGET_CHANGED,
                            canonical_subject=canonical_subj,
                            comparison_status=ComparisonStatus.COMPARED,
                            description=(
                                f"Transition from state '{from_a}' reached target state '{to_a}' in Version A, "
                                f"but reached target state '{to_b}' in Version B."
                            ),
                            evidence=[evidence],
                        )
                    )

            # 2. Ambiguous Transitions
            elif ta.relation == AlignmentRelation.AMBIGUOUS:
                tid_a = ta.transition_a_id or "unknown"
                canonical_subj = f"transition:{tid_a}"
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.TRANSITION,
                    kind=DifferenceKind.TRANSITION_AMBIGUOUS,
                    canonical_subject=canonical_subj,
                    before_identity=tid_a,
                    after_identity="ambiguous",
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=tid_a,
                    after_value=None,
                    transition_a_id=tid_a,
                    source_state_id=ta.from_state_a_id,
                    target_state_id=ta.to_state_a_id,
                    details={"ambiguity_candidates": ta.evidence.ambiguity_candidates},
                    comparison_completeness="ambiguous",
                )
                differences.append(
                    TransitionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.TRANSITION,
                        kind=DifferenceKind.TRANSITION_AMBIGUOUS,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.NOT_COMPARABLE,
                        description=(
                            f"Transition '{tid_a}' from state '{ta.from_state_a_id}' matched multiple candidates in Version B: "
                            f"{', '.join(ta.evidence.ambiguity_candidates)}."
                        ),
                        evidence=[evidence],
                    )
                )

            # 3. Unmatched Transitions within aligned list
            elif ta.relation == AlignmentRelation.UNMATCHED:
                if ta.transition_a_id and not ta.transition_b_id:
                    tid_a = ta.transition_a_id
                    canonical_subj = f"transition:{tid_a}"
                    diff_id = compute_deterministic_diff_id(
                        category=DifferenceCategory.TRANSITION,
                        kind=DifferenceKind.TRANSITION_ONLY_IN_A,
                        canonical_subject=canonical_subj,
                        before_identity=tid_a,
                        after_identity="none",
                    )
                    evidence = DifferenceEvidence(
                        canonical_subject=canonical_subj,
                        before_value=tid_a,
                        after_value=None,
                        transition_a_id=tid_a,
                        source_state_id=ta.from_state_a_id,
                        target_state_id=ta.to_state_a_id,
                        details={"from_state_a": ta.from_state_a_id, "to_state_a": ta.to_state_a_id},
                    )
                    differences.append(
                        TransitionDifference(
                            diff_id=diff_id,
                            category=DifferenceCategory.TRANSITION,
                            kind=DifferenceKind.TRANSITION_ONLY_IN_A,
                            canonical_subject=canonical_subj,
                            comparison_status=ComparisonStatus.COMPARED,
                            description=(
                                f"Transition '{tid_a}' from state '{ta.from_state_a_id}' to '{ta.to_state_a_id}' "
                                f"was executed in Version A but not reached in Version B."
                            ),
                            evidence=[evidence],
                        )
                    )
                elif ta.transition_b_id and not ta.transition_a_id:
                    tid_b = ta.transition_b_id
                    canonical_subj = f"transition:{tid_b}"
                    diff_id = compute_deterministic_diff_id(
                        category=DifferenceCategory.TRANSITION,
                        kind=DifferenceKind.TRANSITION_ONLY_IN_B,
                        canonical_subject=canonical_subj,
                        before_identity="none",
                        after_identity=tid_b,
                    )
                    evidence = DifferenceEvidence(
                        canonical_subject=canonical_subj,
                        before_value=None,
                        after_value=tid_b,
                        transition_b_id=tid_b,
                        source_state_id=ta.from_state_b_id,
                        target_state_id=ta.to_state_b_id,
                        details={"from_state_b": ta.from_state_b_id, "to_state_b": ta.to_state_b_id},
                    )
                    differences.append(
                        TransitionDifference(
                            diff_id=diff_id,
                            category=DifferenceCategory.TRANSITION,
                            kind=DifferenceKind.TRANSITION_ONLY_IN_B,
                            canonical_subject=canonical_subj,
                            comparison_status=ComparisonStatus.COMPARED,
                            description=(
                                f"Additional transition '{tid_b}' from state '{ta.from_state_b_id}' to '{ta.to_state_b_id}' "
                                f"was executed in Version B with no baseline in Version A."
                            ),
                            evidence=[evidence],
                        )
                    )

        return differences
