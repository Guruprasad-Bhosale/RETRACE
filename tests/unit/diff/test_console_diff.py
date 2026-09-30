"""Unit tests for Console Semantic Differ."""

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
from apps.worker.diff.console_diff import ConsoleDiffer
from apps.worker.diff.models import DifferenceCategory, DifferenceKind


def test_console_error_added_and_removed():
    differ = ConsoleDiffer()

    # Case 1: Errors added in Version B
    sig_a1 = StateSignature(
        state_id="st_1",
        normalized_route="/app",
        inventory_signature="i1",
        a11y_signature="a1",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(console_errors_count=0),
    )
    sig_b1 = StateSignature(
        state_id="st_2",
        normalized_route="/app",
        inventory_signature="i1",
        a11y_signature="a1",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(console_errors_count=2),
    )

    sa = StateAlignment(
        state_a_id="st_1",
        state_b_id="st_2",
        signature_a=sig_a1,
        signature_b=sig_b1,
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
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.category == DifferenceCategory.CONSOLE
    assert diff.kind == DifferenceKind.CONSOLE_ERROR_ADDED
    assert diff.evidence[0].before_value == 0
    assert diff.evidence[0].after_value == 2
