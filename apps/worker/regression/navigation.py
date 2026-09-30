"""Navigation Regression Classification Rules.

Detects navigation regressions including disappeared application routes and altered navigation target paths.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class RouteRemovedRule(ClassificationRule):
    """Fires when an accessible application route present in Version A is absent in Version B."""

    rule_id = "NAV-ROUTE-REMOVED"
    category = RegressionCategory.NAVIGATION
    description = "Accessible baseline route was removed or inaccessible in target build."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.ROUTE or diff.kind != DifferenceKind.ROUTE_REMOVED:
            return self.not_applicable()

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=f"Application route '{diff.canonical_subject}' is present in Version A but absent in Version B.",
            evidence=self.extract_evidence(diff),
        )


class TransitionTargetChangedRule(ClassificationRule):
    """Fires when an aligned navigation or click action leads to a different target state."""

    rule_id = "NAV-TRANSITION-TARGET"
    category = RegressionCategory.NAVIGATION
    description = "Action execution resulted in a different destination state."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.TRANSITION or diff.kind != DifferenceKind.TRANSITION_TARGET_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=(
                f"Transition from state '{ev.source_state_id}' reached '{ev.before_value}' in Version A, "
                f"but reached '{ev.after_value}' in Version B."
            ),
            evidence=self.extract_evidence(diff),
        )
