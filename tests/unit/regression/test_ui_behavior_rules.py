"""Unit tests for UI Behavior Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.ui_behavior import (
    ActionDisabledRule,
    ActionRemovedRule,
    ActionTargetChangedRule,
)


def test_action_removed_rule():
    rule = ActionRemovedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_ui_1",
        category=DifferenceCategory.ACTION,
        kind=DifferenceKind.ACTION_REMOVED,
        canonical_subject="action:btn_delete",
        comparison_status=ComparisonStatus.COMPARED,
        description="Delete button removed",
        evidence=[DifferenceEvidence(canonical_subject="action:btn_delete")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.UI_BEHAVIOR


def test_action_disabled_rule():
    rule = ActionDisabledRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_ui_2",
        category=DifferenceCategory.INTERACTION,
        kind=DifferenceKind.ACTION_STATE_CHANGED,
        canonical_subject="action:btn_checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="Checkout disabled",
        evidence=[DifferenceEvidence(canonical_subject="action:btn_checkout", before_value="false", after_value="true")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE


def test_action_target_changed_rule():
    rule = ActionTargetChangedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_ui_3",
        category=DifferenceCategory.ACTION,
        kind=DifferenceKind.ACTION_TARGET_CHANGED,
        canonical_subject="action:link_help",
        comparison_status=ComparisonStatus.COMPARED,
        description="Target ID changed",
        evidence=[DifferenceEvidence(canonical_subject="action:link_help", before_value="target_old", after_value="target_new")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
