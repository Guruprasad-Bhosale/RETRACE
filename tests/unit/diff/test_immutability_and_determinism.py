"""Unit tests for Determinism, Immutability, and Deduplication."""

import copy
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
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.diff.models import DifferenceCategory, DifferenceKind


def test_immutability_of_alignment_result():
    engine = SemanticDiffEngine()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/route_a",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(http_status=200),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/route_a",
        inventory_signature="inv_b",
        a11y_signature="a11y_b",
        ui_state_signature="ui_b",
        observational=StateObservationalFeatures(http_status=500),
    )
    sa = StateAlignment(
        state_a_id="st_1",
        state_b_id="st_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(route_match=True),
    )

    original = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(
            aligned_states=[sa],
            unique_routes_a=["/route_a"],
            unique_routes_b=["/route_a"],
        ),
    )

    snapshot_before = copy.deepcopy(original.model_dump())
    _ = engine.compare(original)
    snapshot_after = original.model_dump()

    assert snapshot_before == snapshot_after


def test_determinism_and_stable_ordering():
    engine = SemanticDiffEngine()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/route_a",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(http_status=200, console_errors_count=0),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/route_a",
        inventory_signature="inv_b",
        a11y_signature="a11y_b",
        ui_state_signature="ui_b",
        observational=StateObservationalFeatures(http_status=500, console_errors_count=3),
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
        alignment=TrajectoryAlignment(
            aligned_states=[sa],
            unique_routes_a=["/route_a", "/route_removed"],
            unique_routes_b=["/route_a", "/route_added"],
        ),
    )

    res1 = engine.compare(align_res)
    res2 = engine.compare(align_res)

    assert len(res1.differences) == len(res2.differences)
    assert [d.diff_id for d in res1.differences] == [d.diff_id for d in res2.differences]
    assert [d.description for d in res1.differences] == [d.description for d in res2.differences]
    assert [d.deterministic_sort_key() for d in res1.differences] == [d.deterministic_sort_key() for d in res2.differences]


def test_hard_deduplication_and_evidence_merging():
    engine = SemanticDiffEngine()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/checkout",
        inventory_signature="inv",
        a11y_signature="a11y",
        ui_state_signature="ui",
        observational=StateObservationalFeatures(http_status=200),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/checkout",
        inventory_signature="inv",
        a11y_signature="a11y",
        ui_state_signature="ui",
        observational=StateObservationalFeatures(http_status=404),
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

    res = engine.compare(align_res)
    http_diffs = [d for d in res.differences if d.kind == DifferenceKind.HTTP_STATUS_CHANGED]
    assert len(http_diffs) == 1
    assert http_diffs[0].category == DifferenceCategory.STATE
