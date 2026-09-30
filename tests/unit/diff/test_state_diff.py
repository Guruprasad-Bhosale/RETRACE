"""Unit tests for State Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
)
from apps.worker.diff.models import DifferenceCategory, DifferenceKind
from apps.worker.diff.state_diff import StateDiffer


def test_state_diff_http_status_and_title():
    differ = StateDiffer()
    sig_a = StateSignature(
        state_id="state_1",
        normalized_route="/checkout",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(http_status=200, page_title="Checkout A"),
    )
    sig_b = StateSignature(
        state_id="state_2",
        normalized_route="/checkout",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(http_status=404, page_title="Checkout B"),
    )

    sa = StateAlignment(
        state_a_id="state_1",
        state_b_id="state_2",
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
    assert DifferenceKind.HTTP_STATUS_CHANGED in kinds
    assert DifferenceKind.PAGE_TITLE_CHANGED in kinds

    http_diff = next(d for d in diffs if d.kind == DifferenceKind.HTTP_STATUS_CHANGED)
    assert http_diff.category == DifferenceCategory.STATE
    assert http_diff.evidence[0].before_value == 200
    assert http_diff.evidence[0].after_value == 404


def test_state_diff_unmatched_and_ambiguous():
    differ = StateDiffer()
    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(
            unmatched_a_states=["st_a_only"],
            unmatched_b_states=["st_b_only"],
            ambiguous_states=[
                StateAlignment(
                    state_a_id="st_ambig",
                    relation=AlignmentRelation.AMBIGUOUS,
                    evidence=MatchEvidence(ambiguity_candidates=["cand_1", "cand_2"]),
                )
            ],
        ),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 3

    kinds = {d.kind for d in diffs}
    assert DifferenceKind.STATE_ONLY_IN_A in kinds
    assert DifferenceKind.STATE_ONLY_IN_B in kinds
    assert DifferenceKind.STATE_AMBIGUOUS in kinds
