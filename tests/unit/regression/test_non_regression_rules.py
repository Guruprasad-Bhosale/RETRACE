"""Unit tests for Non-Regression Rules and Cautious Fallbacks."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.non_regression import PresentationalTextRule


def test_presentational_text_rule_when_explicitly_presentational():
    rule = PresentationalTextRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_nreg_1",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.DOM_TEXT_CHANGED,
        canonical_subject="dom:footer_copyright",
        comparison_status=ComparisonStatus.COMPARED,
        description="Copyright year changed",
        evidence=[
            DifferenceEvidence(
                canonical_subject="dom:footer_copyright",
                before_value="2025",
                after_value="2026",
                details={"is_presentational": True},
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.NON_REGRESSION
    assert rule.category == RegressionCategory.NON_REGRESSION


def test_presentational_text_rule_not_applicable_on_generic_text():
    rule = PresentationalTextRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_nreg_2",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.DOM_TEXT_CHANGED,
        canonical_subject="dom:order_button",
        comparison_status=ComparisonStatus.COMPARED,
        description="Text changed from Place Order to Confirm Purchase",
        evidence=[
            DifferenceEvidence(
                canonical_subject="dom:order_button",
                before_value="Place Order",
                after_value="Confirm Purchase",
                details={},
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    # Generic text change without explicit non-actionable proof is NOT classified as NON_REGRESSION automatically
    assert eval_res.applicable is False
