"""UI Behavior Regression Classification Rules.

Detects user interface behavioral regressions such as missing interactive controls,
disabled action buttons, and altered action target identities.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class ActionRemovedRule(ClassificationRule):
    """Fires when an interactive button, link, or transition present in Version A is removed in Version B."""

    rule_id = "UI-ACTION-REMOVED"
    category = RegressionCategory.UI_BEHAVIOR
    description = "Interactive action control or transition was removed."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind not in (
            DifferenceKind.ACTION_REMOVED,
            DifferenceKind.INTERACTION_ELEMENT_REMOVED,
            DifferenceKind.TRANSITION_ONLY_IN_A,
        ):
            return self.not_applicable()

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=f"Action or interactive element '{diff.canonical_subject}' present in Version A is absent in Version B.",
            evidence=self.extract_evidence(diff),
        )


class ActionDisabledRule(ClassificationRule):
    """Fires when an interactive control becomes disabled in Version B."""

    rule_id = "UI-ACTION-DISABLED"
    category = RegressionCategory.UI_BEHAVIOR
    description = "Action control became disabled or un-interactable."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.INTERACTION or diff.kind != DifferenceKind.ACTION_STATE_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        dis_a = str(ev.before_value).lower() in ("true", "1", "disabled")
        dis_b = str(ev.after_value).lower() in ("true", "1", "disabled")

        if not dis_a and dis_b:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=f"Interactive control '{diff.canonical_subject}' became disabled in Version B.",
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()


class ActionTargetChangedRule(ClassificationRule):
    """Fires when an interactive control's target identity changes."""

    rule_id = "UI-ACTION-TARGET-CHANGED"
    category = RegressionCategory.UI_BEHAVIOR
    description = "Interactive element target identity diverged."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.ACTION_TARGET_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=(
                f"Target identity for action changed from '{ev.before_value if ev else ''}' "
                f"to '{ev.after_value if ev else ''}'."
            ),
            evidence=self.extract_evidence(diff),
        )
