"""Unit tests for Performance Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import PerformancePolicy, RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.performance import NavigationPerformanceRule


def test_performance_slowdown_above_threshold():
    rule = NavigationPerformanceRule()
    config = RegressionConfig(performance=PerformancePolicy(enabled=True, navigation_delta_threshold_ms=500.0))

    diff = SemanticDifference(
        diff_id="d_perf_1",
        category=DifferenceCategory.PERFORMANCE,
        kind=DifferenceKind.NAVIGATION_DURATION_CHANGED,
        canonical_subject="timing:search_action",
        comparison_status=ComparisonStatus.COMPARED,
        description="Duration increased",
        evidence=[
            DifferenceEvidence(
                canonical_subject="timing:search_action",
                before_value="200.0 ms",
                after_value="1200.0 ms",
                details={"delta_ms": 1000.0},
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.PERFORMANCE
    assert "1000.00 ms" in eval_res.reason


def test_performance_slowdown_below_threshold_not_applicable():
    rule = NavigationPerformanceRule()
    config = RegressionConfig(performance=PerformancePolicy(enabled=True, navigation_delta_threshold_ms=500.0))

    diff = SemanticDifference(
        diff_id="d_perf_2",
        category=DifferenceCategory.PERFORMANCE,
        kind=DifferenceKind.NAVIGATION_DURATION_CHANGED,
        canonical_subject="timing:search_action",
        comparison_status=ComparisonStatus.COMPARED,
        description="Duration increased slightly",
        evidence=[
            DifferenceEvidence(
                canonical_subject="timing:search_action",
                before_value="200.0 ms",
                after_value="400.0 ms",
                details={"delta_ms": 200.0},  # 200ms < 500ms
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is False


def test_performance_disabled_unclassified():
    rule = NavigationPerformanceRule()
    config = RegressionConfig(performance=PerformancePolicy(enabled=False))

    diff = SemanticDifference(
        diff_id="d_perf_3",
        category=DifferenceCategory.PERFORMANCE,
        kind=DifferenceKind.NAVIGATION_DURATION_CHANGED,
        canonical_subject="timing:search_action",
        comparison_status=ComparisonStatus.COMPARED,
        description="Duration increased",
        evidence=[
            DifferenceEvidence(
                canonical_subject="timing:search_action",
                before_value="200.0 ms",
                after_value="2000.0 ms",
                details={"delta_ms": 1800.0},
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.UNCLASSIFIED
