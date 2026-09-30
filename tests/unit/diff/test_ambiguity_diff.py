"""Unit tests for Ambiguity and Non-Arbitrary Candidate Handling."""

from uuid import uuid4

from apps.worker.alignment.models import (
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    StateAlignment,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.diff.models import ComparisonStatus, DifferenceKind


def test_ambiguous_state_and_transition_diff():
    engine = SemanticDiffEngine()

    ambig_state = StateAlignment(
        state_a_id="state_ambig",
        relation=AlignmentRelation.AMBIGUOUS,
        evidence=MatchEvidence(ambiguity_candidates=["cand_alpha", "cand_beta"]),
    )

    ambig_trans = TransitionAlignment(
        transition_a_id="trans_ambig",
        from_state_a_id="root",
        relation=AlignmentRelation.AMBIGUOUS,
        evidence=MatchEvidence(ambiguity_candidates=["cand_trans_1", "cand_trans_2"]),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(
            ambiguous_states=[ambig_state],
            aligned_transitions=[ambig_trans],
        ),
    )

    result = engine.compare(align_res)

    kinds = {d.kind for d in result.differences}
    assert DifferenceKind.STATE_AMBIGUOUS in kinds
    assert DifferenceKind.TRANSITION_AMBIGUOUS in kinds

    for d in result.differences:
        if d.kind in (DifferenceKind.STATE_AMBIGUOUS, DifferenceKind.TRANSITION_AMBIGUOUS):
            assert d.comparison_status == ComparisonStatus.NOT_COMPARABLE

    assert len(result.limitations) == 1
    assert "ambiguous structural candidates" in result.limitations[0]
