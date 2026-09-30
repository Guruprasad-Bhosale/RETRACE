"""Unit tests for Action Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.diff.action_diff import ActionDiffer
from apps.worker.diff.models import DifferenceCategory, DifferenceKind
from packages.domain.models import ActionType


def test_action_diff_name_target_and_input_class_changes():
    differ = ActionDiffer()

    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:coupon",
        accessible_name="Apply Coupon",
        normalized_input_class="promo_code",
    )
    sig_b = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:apply_promo",
        accessible_name="Apply",
        normalized_input_class="discount_code",
    )

    act_align = ActionAlignment(
        action_a_id="act_1",
        action_b_id="act_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.PARTIAL_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    ta = TransitionAlignment(
        transition_a_id="trans_1",
        transition_b_id="trans_2",
        from_state_a_id="cart",
        from_state_b_id="cart",
        action_alignment=act_align,
        relation=AlignmentRelation.PARTIAL_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_transitions=[ta]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 3

    kinds = {d.kind for d in diffs}
    assert DifferenceKind.ACTION_NAME_CHANGED in kinds
    assert DifferenceKind.ACTION_TARGET_CHANGED in kinds
    assert DifferenceKind.ACTION_INPUT_BEHAVIOR_CHANGED in kinds

    name_diff = next(d for d in diffs if d.kind == DifferenceKind.ACTION_NAME_CHANGED)
    assert name_diff.category == DifferenceCategory.ACTION
    assert name_diff.evidence[0].before_value == "Apply Coupon"
    assert name_diff.evidence[0].after_value == "Apply"
