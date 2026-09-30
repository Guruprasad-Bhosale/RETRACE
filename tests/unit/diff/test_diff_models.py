"""Unit tests for Diff Domain Models, Serialization, and Deterministic IDs."""

from datetime import UTC, datetime
from uuid import uuid4

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
    compute_deterministic_diff_id,
)


def test_compute_deterministic_diff_id():
    id1 = compute_deterministic_diff_id(
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        before_identity="200",
        after_identity="404",
    )
    id2 = compute_deterministic_diff_id(
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        before_identity="200",
        after_identity="404",
    )
    assert id1 == id2
    assert len(id1) == 16


def test_semantic_difference_serialization():
    diff_id = compute_deterministic_diff_id(
        category=DifferenceCategory.ROUTE,
        kind=DifferenceKind.ROUTE_ADDED,
        canonical_subject="/cart",
        before_identity="none",
        after_identity="/cart",
    )
    diff = SemanticDifference(
        diff_id=diff_id,
        category=DifferenceCategory.ROUTE,
        kind=DifferenceKind.ROUTE_ADDED,
        canonical_subject="/cart",
        comparison_status=ComparisonStatus.COMPARED,
        description="Route /cart added in Version B",
        evidence=[
            DifferenceEvidence(
                canonical_subject="/cart",
                before_value=None,
                after_value="/cart",
                details={"side": "B"},
            )
        ],
    )
    dumped = diff.model_dump()
    assert dumped["diff_id"] == diff_id
    assert dumped["category"] == "ROUTE"
    assert dumped["kind"] == "ROUTE_ADDED"
    assert len(dumped["evidence"]) == 1


def test_timestamp_does_not_affect_deterministic_sort_key():
    diff1 = SemanticDifference(
        diff_id="abc12345",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.DOM_STRUCTURE_CHANGED,
        canonical_subject="dom:/home",
        description="Changed",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    diff2 = SemanticDifference(
        diff_id="abc12345",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.DOM_STRUCTURE_CHANGED,
        canonical_subject="dom:/home",
        description="Changed",
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
    )
    assert diff1.deterministic_sort_key() == diff2.deterministic_sort_key()


def test_semantic_diff_result_serialization():
    run_a = uuid4()
    run_b = uuid4()
    traj_a = uuid4()
    traj_b = uuid4()

    res = SemanticDiffResult(
        run_a_id=run_a,
        run_b_id=run_b,
        trajectory_a_id=traj_a,
        trajectory_b_id=traj_b,
        differences=[],
        summary=SemanticDiffSummary(),
        comparison_statistics={"total_differences": 0},
        limitations=["None"],
    )
    json_data = res.model_dump(mode="json")
    assert json_data["run_a_id"] == str(run_a)
    assert json_data["summary"]["total_differences"] == 0
