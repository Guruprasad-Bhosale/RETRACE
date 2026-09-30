"""Unit tests for Network Semantic Differ."""

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
from apps.worker.diff.network_diff import NetworkDiffer


def test_network_failure_divergence():
    differ = NetworkDiffer()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/api/data",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(network_failures_count=0),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/api/data",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(network_failures_count=3),
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
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.category == DifferenceCategory.NETWORK
    assert diff.kind == DifferenceKind.NETWORK_FAILURE_CHANGED
    assert diff.evidence[0].before_value == 0
    assert diff.evidence[0].after_value == 3
