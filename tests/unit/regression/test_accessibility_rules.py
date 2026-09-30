"""Unit tests for Accessibility Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.accessibility import (
    AccessibilityHashFallbackRule,
    AccessibilityNameRemovedRule,
    AccessibilityRoleChangedRule,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory


def test_a11y_role_changed_rule():
    rule = AccessibilityRoleChangedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_a11y_1",
        category=DifferenceCategory.ACCESSIBILITY,
        kind=DifferenceKind.A11Y_ROLE_CHANGED,
        canonical_subject="a11y:/dialog",
        comparison_status=ComparisonStatus.COMPARED,
        description="Role changed from dialog to div",
        evidence=[DifferenceEvidence(canonical_subject="a11y:/dialog", before_value="dialog", after_value="div")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.ACCESSIBILITY


def test_a11y_name_removed_rule():
    rule = AccessibilityNameRemovedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_a11y_2",
        category=DifferenceCategory.ACTION,
        kind=DifferenceKind.ACTION_NAME_CHANGED,
        canonical_subject="action:btn_close",
        comparison_status=ComparisonStatus.COMPARED,
        description="Accessible name removed",
        evidence=[DifferenceEvidence(canonical_subject="action:btn_close", before_value="Close Window", after_value="")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE


def test_a11y_hash_fallback_rule():
    rule = AccessibilityHashFallbackRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_a11y_3",
        category=DifferenceCategory.ACCESSIBILITY,
        kind=DifferenceKind.A11Y_STRUCTURE_CHANGED,
        canonical_subject="a11y:/home",
        comparison_status=ComparisonStatus.COMPARED,
        description="Hash changed",
        evidence=[DifferenceEvidence(canonical_subject="a11y:/home", before_value="h1", after_value="h2")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.UNCLASSIFIED
    assert "detailed tree evidence" in eval_res.reason
