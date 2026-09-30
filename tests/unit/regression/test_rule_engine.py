"""Unit tests for Rule Engine Execution and Not-Applicable Semantics."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.rule_engine import RuleEngine


def test_rule_engine_not_applicable_filtering():
    engine = RuleEngine()
    config = RegressionConfig()

    # HTTP Status 200 -> 200 (should not fire HttpStatusErrorRule)
    diff = SemanticDifference(
        diff_id="diff_same_status",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/home",
        comparison_status=ComparisonStatus.COMPARED,
        description="Status changed from 200 to 201",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/home",
                before_value=200,
                after_value=201,
            )
        ],
    )

    classifications = engine.evaluate_difference(diff, config)
    # 200 -> 201 is not a regression error; defaults to UNCLASSIFIED without false non-regression
    assert len(classifications) == 1
    assert classifications[0].status == ClassificationStatus.UNCLASSIFIED
    assert classifications[0].rule_id == "DEFAULT-UNCLASSIFIED"


def test_rule_engine_applicable_regression_rule():
    engine = RuleEngine()
    config = RegressionConfig()

    # HTTP Status 200 -> 500
    diff = SemanticDifference(
        diff_id="diff_server_error",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/api/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="Status changed from 200 to 500",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/api/checkout",
                before_value=200,
                after_value=500,
            )
        ],
    )

    classifications = engine.evaluate_difference(diff, config)
    # May trigger functional and api contract rules
    assert len(classifications) >= 1
    assert any(c.status == ClassificationStatus.REGRESSION_CANDIDATE for c in classifications)
    assert any(c.rule_id == "FUNC-HTTP-STATUS-ERROR" for c in classifications)


def test_rule_engine_ambiguity_fallback():
    engine = RuleEngine()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="diff_ambig",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.STATE_AMBIGUOUS,
        canonical_subject="state:ambig_node",
        comparison_status=ComparisonStatus.NOT_COMPARABLE,
        description="Ambiguous state correspondence",
    )

    classifications = engine.evaluate_difference(diff, config)
    assert len(classifications) == 1
    assert classifications[0].status == ClassificationStatus.UNCLASSIFIED
    assert classifications[0].category == RegressionCategory.UNKNOWN
    assert classifications[0].rule_id == "AMBIG-INSUFFICIENT-EVIDENCE"
