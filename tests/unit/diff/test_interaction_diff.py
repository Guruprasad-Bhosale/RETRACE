"""Unit tests for Interaction and DOM Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.diff.interaction_diff import InteractionDiffer
from apps.worker.diff.models import DifferenceKind
from packages.domain.models import ActionType


def test_interaction_dom_hierarchy_and_element_counts():
    differ = InteractionDiffer()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/dashboard",
        inventory_signature="sig_inv_a",
        a11y_signature="a1",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(interactive_elements_count=5),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/dashboard",
        inventory_signature="sig_inv_b",
        a11y_signature="a1",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(interactive_elements_count=8),
    )

    sa = StateAlignment(
        state_a_id="st_1",
        state_b_id="st_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(route_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_states=[sa]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 2

    kinds = {d.kind for d in diffs}
    assert DifferenceKind.DOM_STRUCTURE_CHANGED in kinds
    assert DifferenceKind.INTERACTION_ELEMENT_ADDED in kinds


def test_form_attribute_required_and_disabled_changes():
    differ = InteractionDiffer()

    sig_a = ActionSignature(
        action_type=ActionType.TYPE,
        stable_target_identity="input:email",
        semantic_attributes={"required": "false", "disabled": "false"},
    )
    sig_b = ActionSignature(
        action_type=ActionType.TYPE,
        stable_target_identity="input:email",
        semantic_attributes={"required": "true", "disabled": "true"},
    )

    act_align = ActionAlignment(
        action_a_id="act_1",
        action_b_id="act_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    ta = TransitionAlignment(
        transition_a_id="t1",
        transition_b_id="t2",
        action_alignment=act_align,
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
    assert len(diffs) == 2

    kinds = {d.kind for d in diffs}
    assert DifferenceKind.FORM_REQUIRED_CHANGED in kinds
    assert DifferenceKind.ACTION_STATE_CHANGED in kinds
