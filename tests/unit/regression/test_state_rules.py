"""Unit tests for State Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.state import (
    ActionDisabledConstraintRule,
    FormRequiredConstraintRule,
    MissingStateContextualRule,
)


def test_form_required_constraint_rule():
    rule = FormRequiredConstraintRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_st_1",
        category=DifferenceCategory.DOM,
        kind=DifferenceKind.FORM_REQUIRED_CHANGED,
        canonical_subject="action:input_phone",
        comparison_status=ComparisonStatus.COMPARED,
        description="Phone field required",
        evidence=[DifferenceEvidence(canonical_subject="action:input_phone", before_value="false", after_value="true")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.STATE


def test_action_disabled_rule():
    rule = ActionDisabledConstraintRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_st_2",
        category=DifferenceCategory.INTERACTION,
        kind=DifferenceKind.ACTION_STATE_CHANGED,
        canonical_subject="action:submit_btn",
        comparison_status=ComparisonStatus.COMPARED,
        description="Button disabled",
        evidence=[DifferenceEvidence(canonical_subject="action:submit_btn", before_value="false", after_value="true")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE


def test_missing_state_contextual_rule():
    rule = MissingStateContextualRule()
    config = RegressionConfig()

    # Case 1: Bare unmatched state without transition error evidence -> UNCLASSIFIED
    diff_bare = SemanticDifference(
        diff_id="d_st_3",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.STATE_ONLY_IN_A,
        canonical_subject="state:state_123",
        comparison_status=ComparisonStatus.COMPARED,
        description="State in A only",
        evidence=[DifferenceEvidence(canonical_subject="state:state_123", details={})],
    )
    eval_bare = rule.evaluate(diff_bare, config)
    assert eval_bare.applicable is True
    assert eval_bare.status == ClassificationStatus.UNCLASSIFIED

    # Case 2: Unmatched state with transition failure context -> REGRESSION_CANDIDATE
    diff_fail = SemanticDifference(
        diff_id="d_st_4",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.STATE_ONLY_IN_A,
        canonical_subject="state:state_456",
        comparison_status=ComparisonStatus.COMPARED,
        description="State in A only with transition failure",
        evidence=[DifferenceEvidence(canonical_subject="state:state_456", details={"transition_failure": True})],
    )
    eval_fail = rule.evaluate(diff_fail, config)
    assert eval_fail.applicable is True
    assert eval_fail.status == ClassificationStatus.REGRESSION_CANDIDATE
