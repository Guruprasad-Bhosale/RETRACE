"""Unit tests for Alignment Domain Models serialization and JSON round-trips."""

from uuid import uuid4

from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    EvidenceStrength,
    MatchEvidence,
    StateAlignment,
    StateSignature,
    TrajectoryAlignment,
    TransitionAlignment,
)
from packages.domain.models import ActionType


def test_alignment_result_json_roundtrip() -> None:
    run_a = uuid4()
    run_b = uuid4()
    traj_a = uuid4()
    traj_b = uuid4()

    act_sig = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn-1",
    )
    act_align = ActionAlignment(
        action_a_id="t1",
        action_b_id="t2",
        signature_a=act_sig,
        signature_b=act_sig,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(evidence_strength=EvidenceStrength.EXACT),
    )

    state_sig = StateSignature(
        state_id="s1",
        normalized_route="/",
        inventory_signature="inv",
        a11y_signature="a11y",
        ui_state_signature="ui",
    )
    st_align = StateAlignment(
        state_a_id="s1",
        state_b_id="s1",
        signature_a=state_sig,
        signature_b=state_sig,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(evidence_strength=EvidenceStrength.EXACT),
    )

    trans_align = TransitionAlignment(
        transition_a_id="t1",
        transition_b_id="t2",
        from_state_a_id="s1",
        from_state_b_id="s1",
        to_state_a_id="s2",
        to_state_b_id="s2",
        action_alignment=act_align,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(evidence_strength=EvidenceStrength.EXACT),
    )

    traj_align = TrajectoryAlignment(
        aligned_states=[st_align],
        aligned_transitions=[trans_align],
        unmatched_a_states=[],
        unmatched_b_states=[],
        unique_routes_a=["/"],
        unique_routes_b=["/"],
        aligned_routes_count=1,
    )

    res = AlignmentResult(
        run_a_id=run_a,
        run_b_id=run_b,
        trajectory_a_id=traj_a,
        trajectory_b_id=traj_b,
        alignment=traj_align,
    )

    json_data = res.model_dump_json()
    assert str(run_a) in json_data

    loaded = AlignmentResult.model_validate_json(json_data)
    assert loaded.run_a_id == run_a
    assert loaded.alignment.aligned_states[0].state_a_id == "s1"
