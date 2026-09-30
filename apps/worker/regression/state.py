"""State Regression Classification Rules.

Detects state and form-level regressions including unexpectedly required form fields,
disabled actionable controls, and contextual missing states.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class FormRequiredConstraintRule(ClassificationRule):
    """Fires when a previously optional form field becomes strictly required."""

    rule_id = "STATE-FORM-REQUIRED"
    category = RegressionCategory.STATE
    description = "Form field constraint unexpectedly changed to required."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.FORM_REQUIRED_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        req_a = str(ev.before_value).lower() in ("true", "1", "required")
        req_b = str(ev.after_value).lower() in ("true", "1", "required")

        if not req_a and req_b:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=f"Form input '{diff.canonical_subject}' became required in Version B.",
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()


class ActionDisabledConstraintRule(ClassificationRule):
    """Fires when a previously enabled interactive control becomes disabled."""

    rule_id = "STATE-ACTION-DISABLED"
    category = RegressionCategory.STATE
    description = "Interactive control unexpectedly changed from enabled to disabled."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.ACTION_STATE_CHANGED:
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
                reason=f"Actionable control '{diff.canonical_subject}' became disabled in Version B.",
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()


class MissingStateContextualRule(ClassificationRule):
    """Evaluates unmatched states, requiring contextual transition failure evidence to classify as regression candidate."""

    rule_id = "STATE-MISSING-TRANSITION"
    category = RegressionCategory.STATE
    description = "Baseline state missing in target version evaluated with contextual transition evidence."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.STATE or diff.kind != DifferenceKind.STATE_ONLY_IN_A:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        details = ev.details if ev else {}

        # If contextual error details or transition failures are recorded in details:
        if details.get("transition_failure") or details.get("error_context"):
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"State '{diff.canonical_subject}' present in Version A failed to be reached in Version B "
                    f"due to transition failure."
                ),
                evidence=self.extract_evidence(diff),
            )

        # Unmatched state without explicit failure evidence remains UNCLASSIFIED
        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.UNCLASSIFIED,
            reason=f"State '{diff.canonical_subject}' exists only in Version A without contextual transition failure evidence.",
            evidence=self.extract_evidence(diff),
        )
