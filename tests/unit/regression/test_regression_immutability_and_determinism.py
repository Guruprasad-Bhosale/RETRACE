"""Unit tests for Regression Classifier Determinism and Immutability."""

import copy
from uuid import uuid4

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
)
from apps.worker.regression.classifier import RegressionClassifier


def test_immutability_of_semantic_diff_result():
    classifier = RegressionClassifier()

    diff = SemanticDifference(
        diff_id="diff_1",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="200 -> 500",
        evidence=[DifferenceEvidence(canonical_subject="state:/checkout", before_value=200, after_value=500)],
    )

    diff_res = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff],
        summary=SemanticDiffSummary(total_differences=1),
    )

    snapshot_before = copy.deepcopy(diff_res.model_dump())
    _ = classifier.classify(diff_res)
    snapshot_after = diff_res.model_dump()

    assert snapshot_before == snapshot_after


def test_determinism_and_stable_classification_order():
    classifier = RegressionClassifier()

    diff1 = SemanticDifference(
        diff_id="diff_a",
        category=DifferenceCategory.ROUTE,
        kind=DifferenceKind.ROUTE_REMOVED,
        canonical_subject="/cart",
        comparison_status=ComparisonStatus.COMPARED,
        description="Route removed",
        evidence=[DifferenceEvidence(canonical_subject="/cart")],
    )
    diff2 = SemanticDifference(
        diff_id="diff_b",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="200 -> 500",
        evidence=[DifferenceEvidence(canonical_subject="state:/checkout", before_value=200, after_value=500)],
    )

    diff_res = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff1, diff2],
        summary=SemanticDiffSummary(total_differences=2),
    )

    res1 = classifier.classify(diff_res)
    res2 = classifier.classify(diff_res)

    assert len(res1.classifications) == len(res2.classifications)
    assert [c.classification_id for c in res1.classifications] == [c.classification_id for c in res2.classifications]
    assert [c.deterministic_sort_key() for c in res1.classifications] == [c.deterministic_sort_key() for c in res2.classifications]
