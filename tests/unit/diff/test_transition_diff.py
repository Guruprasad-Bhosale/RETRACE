"""Unit tests for Transition Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.diff.models import DifferenceCategory, DifferenceKind
from apps.worker.diff.transition_diff import TransitionDiffer


def test_transition_target_changed():
    differ = TransitionDiffer()

    ta = TransitionAlignment(
        transition_a_id="t_1",
        transition_b_id="t_2",
        from_state_a_id="cart_state",
        from_state_b_id="cart_state",
        to_state_a_id="checkout_success",
        to_state_b_id="checkout_404_error",
        relation=AlignmentRelation.EXACT_MATCH,
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
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.category == DifferenceCategory.TRANSITION
    assert diff.kind == DifferenceKind.TRANSITION_TARGET_CHANGED
    assert diff.evidence[0].before_value == "checkout_success"
    assert diff.evidence[0].after_value == "checkout_404_error"
    assert diff.evidence[0].source_state_id == "cart_state"


def test_transition_unmatched_and_ambiguous():
    differ = TransitionDiffer()

    ta_unmatched_a = TransitionAlignment(
        transition_a_id="t_a_only",
        from_state_a_id="root",
        to_state_a_id="cart",
        relation=AlignmentRelation.UNMATCHED,
        evidence=MatchEvidence(),
    )
    ta_unmatched_b = TransitionAlignment(
        transition_b_id="t_b_only",
        from_state_b_id="root",
        to_state_b_id="search",
        relation=AlignmentRelation.UNMATCHED,
        evidence=MatchEvidence(),
    )
    ta_ambig = TransitionAlignment(
        transition_a_id="t_ambig",
        from_state_a_id="root",
        to_state_a_id="dest",
        relation=AlignmentRelation.AMBIGUOUS,
        evidence=MatchEvidence(ambiguity_candidates=["cand_x", "cand_y"]),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_transitions=[ta_unmatched_a, ta_unmatched_b, ta_ambig]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 3
    kinds = {d.kind for d in diffs}
    assert DifferenceKind.TRANSITION_ONLY_IN_A in kinds
    assert DifferenceKind.TRANSITION_ONLY_IN_B in kinds
    assert DifferenceKind.TRANSITION_AMBIGUOUS in kinds
