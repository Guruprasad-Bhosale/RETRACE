"""Unit tests for Runtime Error Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig, RuntimeErrorPolicy
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.runtime import (
    ConsoleErrorAddedRule,
    ConsoleWarningRule,
    PageErrorAddedRule,
)


def test_page_error_added_rule():
    rule = PageErrorAddedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_rt_1",
        category=DifferenceCategory.CONSOLE,
        kind=DifferenceKind.PAGE_ERROR_ADDED,
        canonical_subject="console:/home",
        comparison_status=ComparisonStatus.COMPARED,
        description="Unhandled exception",
        evidence=[DifferenceEvidence(canonical_subject="console:/home")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.RUNTIME_ERROR


def test_console_error_added_rule():
    rule = ConsoleErrorAddedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_rt_2",
        category=DifferenceCategory.CONSOLE,
        kind=DifferenceKind.CONSOLE_ERROR_ADDED,
        canonical_subject="console:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="Console error count increased",
        evidence=[DifferenceEvidence(canonical_subject="console:/checkout", before_value=0, after_value=2)],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE


def test_console_warning_rule_unclassified_by_default():
    rule = ConsoleWarningRule()
    config = RegressionConfig(runtime=RuntimeErrorPolicy(treat_warnings_as_candidates=False))

    diff = SemanticDifference(
        diff_id="d_rt_3",
        category=DifferenceCategory.CONSOLE,
        kind=DifferenceKind.CONSOLE_WARNING_CHANGED,
        canonical_subject="console:/app",
        comparison_status=ComparisonStatus.COMPARED,
        description="Warning count diverged",
        evidence=[DifferenceEvidence(canonical_subject="console:/app", before_value=1, after_value=4)],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.UNCLASSIFIED
