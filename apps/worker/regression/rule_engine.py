"""Deterministic Rule Engine for Regression Classification.

Coordinates rule registration, sequential evaluation, and default fallback resolution.
"""

from apps.worker.diff.models import ComparisonStatus, SemanticDifference
from apps.worker.regression.accessibility import (
    AccessibilityHashFallbackRule,
    AccessibilityNameRemovedRule,
    AccessibilityRoleChangedRule,
)
from apps.worker.regression.api_contract import (
    ApiRequestFailureRule,
    ApiRequestStatusErrorRule,
)
from apps.worker.regression.calculation import CalculationOutputChangedRule
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.functional import (
    HttpStatusErrorRule,
    TransitionTargetErrorRule,
)
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    compute_deterministic_classification_id,
)
from apps.worker.regression.navigation import (
    RouteRemovedRule,
    TransitionTargetChangedRule,
)
from apps.worker.regression.non_regression import PresentationalTextRule
from apps.worker.regression.performance import (
    NavigationPerformanceRule,
    StabilizationPerformanceRule,
)
from apps.worker.regression.rules import ClassificationRule
from apps.worker.regression.runtime import (
    ConsoleErrorAddedRule,
    ConsoleWarningRule,
    PageErrorAddedRule,
)
from apps.worker.regression.state import (
    ActionDisabledConstraintRule,
    FormRequiredConstraintRule,
    MissingStateContextualRule,
)
from apps.worker.regression.ui_behavior import (
    ActionDisabledRule,
    ActionRemovedRule,
    ActionTargetChangedRule,
)


class RuleEngine:
    """Manages deterministic rule execution across semantic differences."""

    def __init__(self) -> None:
        self.rules: list[ClassificationRule] = [
            # Functional
            HttpStatusErrorRule(),
            TransitionTargetErrorRule(),
            # Navigation
            RouteRemovedRule(),
            TransitionTargetChangedRule(),
            # API Contract
            ApiRequestFailureRule(),
            ApiRequestStatusErrorRule(),
            # State
            FormRequiredConstraintRule(),
            ActionDisabledConstraintRule(),
            MissingStateContextualRule(),
            # Calculation
            CalculationOutputChangedRule(),
            # Accessibility
            AccessibilityRoleChangedRule(),
            AccessibilityNameRemovedRule(),
            AccessibilityHashFallbackRule(),
            # Performance
            NavigationPerformanceRule(),
            StabilizationPerformanceRule(),
            # Runtime
            PageErrorAddedRule(),
            ConsoleErrorAddedRule(),
            ConsoleWarningRule(),
            # UI Behavior
            ActionRemovedRule(),
            ActionDisabledRule(),
            ActionTargetChangedRule(),
            # Non-Regression
            PresentationalTextRule(),
        ]

    def evaluate_difference(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> list[RegressionClassification]:
        """Evaluate a single SemanticDifference through all registered rules."""
        # 1. Ambiguous / Not Comparable semantic differences remain UNCLASSIFIED
        if diff.comparison_status == ComparisonStatus.NOT_COMPARABLE:
            rule_id = "AMBIG-INSUFFICIENT-EVIDENCE"
            category = RegressionCategory.UNKNOWN
            cid = compute_deterministic_classification_id(diff.diff_id, category, rule_id)
            ev = ClassificationRule.extract_evidence(diff)
            return [
                RegressionClassification(
                    classification_id=cid,
                    difference_id=diff.diff_id,
                    status=ClassificationStatus.UNCLASSIFIED,
                    category=category,
                    rule_id=rule_id,
                    reason=f"Semantic difference '{diff.canonical_subject}' could not be uniquely established (ambiguous alignment).",
                    evidence=ev,
                )
            ]

        classifications: list[RegressionClassification] = []

        # 2. Sequential Rule Evaluation
        for rule in self.rules:
            eval_result = rule.evaluate(diff, config)
            if eval_result.applicable and eval_result.evidence is not None:
                cid = compute_deterministic_classification_id(diff.diff_id, rule.category, rule.rule_id)
                classifications.append(
                    RegressionClassification(
                        classification_id=cid,
                        difference_id=diff.diff_id,
                        status=eval_result.status,
                        category=rule.category,
                        rule_id=rule.rule_id,
                        reason=eval_result.reason,
                        evidence=eval_result.evidence,
                    )
                )
                if not config.classification.allow_multiple_classifications_per_diff:
                    break

        # 3. Default fallback if no deterministic rule fired
        if not classifications:
            rule_id = "DEFAULT-UNCLASSIFIED"
            category = RegressionCategory.UNKNOWN
            cid = compute_deterministic_classification_id(diff.diff_id, category, rule_id)
            ev = ClassificationRule.extract_evidence(diff)
            classifications.append(
                RegressionClassification(
                    classification_id=cid,
                    difference_id=diff.diff_id,
                    status=ClassificationStatus.UNCLASSIFIED,
                    category=category,
                    rule_id=rule_id,
                    reason=f"No deterministic regression rule fired for difference kind '{diff.kind.value}'.",
                    evidence=ev,
                )
            )

        return classifications
