"""Unit tests for API Contract Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.api_contract import (
    ApiRequestFailureRule,
    ApiRequestStatusErrorRule,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory


def test_api_request_failure_rule():
    rule = ApiRequestFailureRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_net_1",
        category=DifferenceCategory.NETWORK,
        kind=DifferenceKind.NETWORK_FAILURE_CHANGED,
        canonical_subject="network:/api/items",
        comparison_status=ComparisonStatus.COMPARED,
        description="Network failures increased",
        evidence=[
            DifferenceEvidence(
                canonical_subject="network:/api/items",
                before_value=0,
                after_value=2,
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.API_CONTRACT


def test_api_request_status_error_rule():
    rule = ApiRequestStatusErrorRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_api_2",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/api/coupon",
        comparison_status=ComparisonStatus.COMPARED,
        description="API returned 422",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/api/coupon",
                before_value=200,
                after_value=422,
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.API_CONTRACT
