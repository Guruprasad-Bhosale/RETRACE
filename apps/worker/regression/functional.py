"""Functional Regression Classification Rules.

Detects functional regressions such as HTTP status code degradations (2xx -> 4xx/5xx)
and directed transition target failures.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class HttpStatusErrorRule(ClassificationRule):
    """Fires when an HTTP status code degrades from successful (2xx/3xx) to client/server error (4xx/5xx)."""

    rule_id = "FUNC-HTTP-STATUS-ERROR"
    category = RegressionCategory.FUNCTIONAL
    description = "HTTP response degraded from successful to client/server error code."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.HTTP_STATUS_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        try:
            status_a = int(ev.before_value) if ev.before_value is not None else None
            status_b = int(ev.after_value) if ev.after_value is not None else None
        except (ValueError, TypeError):
            return self.not_applicable()

        if status_a is not None and status_b is not None:
            is_success_a = 200 <= status_a < 400
            is_error_b = status_b >= 400

            if is_success_a and is_error_b:
                return RuleEvaluation(
                    applicable=True,
                    status=ClassificationStatus.REGRESSION_CANDIDATE,
                    reason=(
                        f"HTTP status code degraded at route '{diff.canonical_subject}': "
                        f"Version A returned HTTP {status_a}, but Version B returned HTTP {status_b}."
                    ),
                    evidence=self.extract_evidence(diff, {"status_a": status_a, "status_b": status_b}),
                )

        return self.not_applicable()


class TransitionTargetErrorRule(ClassificationRule):
    """Fires when a directed user interaction reaches an error target state in Version B."""

    rule_id = "FUNC-TRANSITION-TARGET-ERROR"
    category = RegressionCategory.FUNCTIONAL
    description = "Directed interaction transition terminated at an unexpected failure target state."

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

        to_b = str(ev.after_value or "").lower()
        if any(err_marker in to_b for err_marker in ("error", "404", "500", "fail")):
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"Transition from source state '{ev.source_state_id}' reached failure target '{ev.after_value}' in Version B."
                ),
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()
