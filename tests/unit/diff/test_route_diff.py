"""Unit tests for Route Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import AlignmentResult, TrajectoryAlignment
from apps.worker.diff.models import DifferenceCategory, DifferenceKind
from apps.worker.diff.route_diff import RouteDiffer


def test_route_added_and_removed():
    differ = RouteDiffer()

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(
            unique_routes_a=["http://localhost:3000/home", "http://localhost:3000/legacy-cart"],
            unique_routes_b=["http://localhost:3001/home", "http://localhost:3001/new-checkout"],
        ),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 2

    kinds = {d.kind for d in diffs}
    assert DifferenceKind.ROUTE_REMOVED in kinds
    assert DifferenceKind.ROUTE_ADDED in kinds

    removed = next(d for d in diffs if d.kind == DifferenceKind.ROUTE_REMOVED)
    assert removed.category == DifferenceCategory.ROUTE
    assert removed.canonical_subject == "/legacy-cart"

    added = next(d for d in diffs if d.kind == DifferenceKind.ROUTE_ADDED)
    assert added.category == DifferenceCategory.ROUTE
    assert added.canonical_subject == "/new-checkout"
