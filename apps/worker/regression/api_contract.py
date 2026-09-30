"""API Contract Regression Classification Rules.

Detects network-level regressions, failed HTTP API requests, and status code degradations.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class ApiRequestFailureRule(ClassificationRule):
    """Fires when network request failures increase in Version B."""

    rule_id = "API-REQUEST-FAILURE"
    category = RegressionCategory.API_CONTRACT
    description = "Observed HTTP network request failures increased in target version."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.NETWORK or diff.kind != DifferenceKind.NETWORK_FAILURE_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        try:
            fails_a = int(ev.before_value) if ev.before_value is not None else 0
            fails_b = int(ev.after_value) if ev.after_value is not None else 0
        except (ValueError, TypeError):
            return self.not_applicable()

        if fails_b > fails_a:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"Network request failures increased at route '{diff.canonical_subject}': "
                    f"Version A recorded {fails_a} failure(s), Version B recorded {fails_b} failure(s)."
                ),
                evidence=self.extract_evidence(diff, {"failures_a": fails_a, "failures_b": fails_b}),
            )

        return self.not_applicable()


class ApiRequestStatusErrorRule(ClassificationRule):
    """Fires when an API network request status code changes to a 4xx/5xx error."""

    rule_id = "API-REQUEST-STATUS-ERROR"
    category = RegressionCategory.API_CONTRACT
    description = "API endpoint returned an HTTP client/server error response."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind not in (DifferenceKind.NETWORK_STATUS_CHANGED, DifferenceKind.HTTP_STATUS_CHANGED):
            return self.not_applicable()

        # Check if canonical subject or route indicates an API endpoint
        if "/api/" not in diff.canonical_subject.lower() and diff.category != DifferenceCategory.NETWORK:
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
            if status_a < 400 and status_b >= 400:
                return RuleEvaluation(
                    applicable=True,
                    status=ClassificationStatus.REGRESSION_CANDIDATE,
                    reason=(
                        f"API interaction at '{diff.canonical_subject}' failed: "
                        f"Version A returned HTTP {status_a}, Version B returned HTTP {status_b}."
                    ),
                    evidence=self.extract_evidence(diff, {"status_a": status_a, "status_b": status_b}),
                )

        return self.not_applicable()
