"""Unit tests for Calculation Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.calculation import CalculationOutputChangedRule
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory


def test_calculation_output_changed_rule():
    rule = CalculationOutputChangedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_calc_1",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.FORM_VALUE_CHANGED,
        canonical_subject="action:total_amount",
        comparison_status=ComparisonStatus.COMPARED,
        description="Total calculation diverged",
        evidence=[
            DifferenceEvidence(
                canonical_subject="action:total_amount",
                before_value="110.00",
                after_value="120.00",
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.CALCULATION
    assert "110.00" in eval_res.reason
    assert "120.00" in eval_res.reason
