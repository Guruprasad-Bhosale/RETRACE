"""Unit tests for Functional Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.functional import (
    HttpStatusErrorRule,
    TransitionTargetErrorRule,
)
from apps.worker.regression.models import ClassificationStatus, RegressionCategory


def test_http_status_error_rule_triggers_on_error_status():
    rule = HttpStatusErrorRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d1",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="HTTP 200 -> 404",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/checkout",
                before_value=200,
                after_value=404,
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.FUNCTIONAL
    assert "HTTP 200" in eval_res.reason
    assert "HTTP 404" in eval_res.reason


def test_http_status_error_rule_not_applicable_on_success():
    rule = HttpStatusErrorRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d2",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="HTTP 200 -> 200",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/checkout",
                before_value=200,
                after_value=200,
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is False


def test_transition_target_error_rule():
    rule = TransitionTargetErrorRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d3",
        category=DifferenceCategory.TRANSITION,
        kind=DifferenceKind.TRANSITION_TARGET_CHANGED,
        canonical_subject="transition:cart->checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="Target state changed",
        evidence=[
            DifferenceEvidence(
                canonical_subject="transition:cart->checkout",
                before_value="checkout_success",
                after_value="state_500_error",
                source_state_id="cart",
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
