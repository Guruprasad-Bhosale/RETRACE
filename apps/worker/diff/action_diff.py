"""Action Semantic Difference Analyzer.

Extracts deterministic differences in interactive elements, target identities,
accessible names, input classifications, and actionable states.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ActionDifference,
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class ActionDiffer:
    """Compares aligned interactive actions and detects behavioral/interface modifications."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[ActionDifference]:
        """Extract deterministic action differences from an AlignmentResult."""
        if not self.config.enable_action_diff:
            return []

        differences: list[ActionDifference] = []
        align = alignment_result.alignment

        for ta in align.aligned_transitions:
            act_align = ta.action_alignment
            if not act_align or act_align.relation not in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                continue

            sig_a = act_align.signature_a
            sig_b = act_align.signature_b
            if not sig_a or not sig_b:
                continue

            canonical_subj = f"action:{sig_a.action_type.value}:{sig_a.stable_target_identity}"

            # 1. Accessible Name Changed
            name_a = DiffNormalizer.normalize_text(sig_a.accessible_name)
            name_b = DiffNormalizer.normalize_text(sig_b.accessible_name)
            if name_a and name_b and name_a != name_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ACTION,
                    kind=DifferenceKind.ACTION_NAME_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=name_a,
                    after_identity=name_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=sig_a.accessible_name,
                    after_value=sig_b.accessible_name,
                    action_a_id=act_align.action_a_id,
                    action_b_id=act_align.action_b_id,
                    transition_a_id=ta.transition_a_id,
                    transition_b_id=ta.transition_b_id,
                    source_state_id=ta.from_state_a_id,
                    target_state_id=ta.to_state_a_id,
                    details={"accessible_name_a": sig_a.accessible_name, "accessible_name_b": sig_b.accessible_name},
                )
                differences.append(
                    ActionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ACTION,
                        kind=DifferenceKind.ACTION_NAME_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Action accessible name changed for '{sig_a.stable_target_identity}': "
                            f"Version A was '{sig_a.accessible_name}', Version B is '{sig_b.accessible_name}'."
                        ),
                        evidence=[evidence],
                    )
                )

            # 2. Stable Target Identity Changed
            if sig_a.stable_target_identity != sig_b.stable_target_identity:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ACTION,
                    kind=DifferenceKind.ACTION_TARGET_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=sig_a.stable_target_identity,
                    after_identity=sig_b.stable_target_identity,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=sig_a.stable_target_identity,
                    after_value=sig_b.stable_target_identity,
                    action_a_id=act_align.action_a_id,
                    action_b_id=act_align.action_b_id,
                    transition_a_id=ta.transition_a_id,
                    transition_b_id=ta.transition_b_id,
                    source_state_id=ta.from_state_a_id,
                    target_state_id=ta.to_state_a_id,
                    details={"target_a": sig_a.stable_target_identity, "target_b": sig_b.stable_target_identity},
                )
                differences.append(
                    ActionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ACTION,
                        kind=DifferenceKind.ACTION_TARGET_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Action target identity changed: "
                            f"Version A targeted '{sig_a.stable_target_identity}', Version B targeted '{sig_b.stable_target_identity}'."
                        ),
                        evidence=[evidence],
                    )
                )

            # 3. Normalized Input Behavior Changed
            if (
                sig_a.normalized_input_class
                and sig_b.normalized_input_class
                and sig_a.normalized_input_class != sig_b.normalized_input_class
            ):
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ACTION,
                    kind=DifferenceKind.ACTION_INPUT_BEHAVIOR_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=sig_a.normalized_input_class,
                    after_identity=sig_b.normalized_input_class,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=sig_a.normalized_input_class,
                    after_value=sig_b.normalized_input_class,
                    action_a_id=act_align.action_a_id,
                    action_b_id=act_align.action_b_id,
                    transition_a_id=ta.transition_a_id,
                    transition_b_id=ta.transition_b_id,
                    source_state_id=ta.from_state_a_id,
                    target_state_id=ta.to_state_a_id,
                    details={"input_class_a": sig_a.normalized_input_class, "input_class_b": sig_b.normalized_input_class},
                )
                differences.append(
                    ActionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ACTION,
                        kind=DifferenceKind.ACTION_INPUT_BEHAVIOR_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Input classification changed for '{sig_a.stable_target_identity}': "
                            f"Version A classified as '{sig_a.normalized_input_class}', Version B as '{sig_b.normalized_input_class}'."
                        ),
                        evidence=[evidence],
                    )
                )

        return differences
