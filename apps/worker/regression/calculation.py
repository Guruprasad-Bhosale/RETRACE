"""Calculation Regression Classification Rules.

Detects calculation and derived output regressions where equivalent inputs produce divergent computed values.
"""

from apps.worker.diff.models import DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class CalculationOutputChangedRule(ClassificationRule):
    """Fires when calculated form or displayed numerical output differs under equivalent inputs."""

    rule_id = "CALC-OUTPUT-CHANGED"
    category = RegressionCategory.CALCULATION
    description = "Derived calculation or form value output diverged between versions."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.FORM_VALUE_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev or ev.before_value is None or ev.after_value is None:
            return self.not_applicable()

        if ev.before_value != ev.after_value:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"Computed value diverged for '{diff.canonical_subject}': "
                    f"Version A produced '{ev.before_value}', Version B produced '{ev.after_value}'."
                ),
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()
