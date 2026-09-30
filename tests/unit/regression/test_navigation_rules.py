"""Unit tests for Navigation Regression Rules."""

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
)
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import ClassificationStatus, RegressionCategory
from apps.worker.regression.navigation import (
    RouteRemovedRule,
    TransitionTargetChangedRule,
)


def test_route_removed_rule():
    rule = RouteRemovedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_nav_1",
        category=DifferenceCategory.ROUTE,
        kind=DifferenceKind.ROUTE_REMOVED,
        canonical_subject="/settings",
        comparison_status=ComparisonStatus.COMPARED,
        description="Route removed",
        evidence=[DifferenceEvidence(canonical_subject="/settings", before_value="/settings")],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
    assert rule.category == RegressionCategory.NAVIGATION


def test_transition_target_changed_navigation_rule():
    rule = TransitionTargetChangedRule()
    config = RegressionConfig()

    diff = SemanticDifference(
        diff_id="d_nav_2",
        category=DifferenceCategory.TRANSITION,
        kind=DifferenceKind.TRANSITION_TARGET_CHANGED,
        canonical_subject="transition:home->about",
        comparison_status=ComparisonStatus.COMPARED,
        description="Target changed",
        evidence=[
            DifferenceEvidence(
                canonical_subject="transition:home->about",
                before_value="about_page",
                after_value="contact_page",
                source_state_id="home",
            )
        ],
    )

    eval_res = rule.evaluate(diff, config)
    assert eval_res.applicable is True
    assert eval_res.status == ClassificationStatus.REGRESSION_CANDIDATE
