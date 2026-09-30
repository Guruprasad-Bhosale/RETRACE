"""Runtime Error Regression Classification Rules.

Detects unhandled page exceptions, console error count increases, and script failures.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class PageErrorAddedRule(ClassificationRule):
    """Fires when unhandled JavaScript runtime exceptions are thrown."""

    rule_id = "RUNTIME-PAGE-ERROR"
    category = RegressionCategory.RUNTIME_ERROR
    description = "Unhandled JavaScript runtime error occurred in target application."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind != DifferenceKind.PAGE_ERROR_ADDED:
            return self.not_applicable()

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=f"Unhandled runtime script error occurred at '{diff.canonical_subject}'.",
            evidence=self.extract_evidence(diff),
        )


class ConsoleErrorAddedRule(ClassificationRule):
    """Fires when console error message count increases in Version B."""

    rule_id = "RUNTIME-CONSOLE-ERROR"
    category = RegressionCategory.RUNTIME_ERROR
    description = "Console error count increased in target version."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.CONSOLE or diff.kind != DifferenceKind.CONSOLE_ERROR_ADDED:
            return self.not_applicable()

        if not config.runtime.treat_console_errors_as_candidates:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.UNCLASSIFIED,
                reason="Console errors are configured to be unclassified.",
                evidence=self.extract_evidence(diff),
            )

        ev = diff.evidence[0] if diff.evidence else None
        err_a = ev.before_value if ev else 0
        err_b = ev.after_value if ev else 0

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=(
                f"Console error count increased at route '{diff.canonical_subject}': "
                f"Version A logged {err_a} error(s), Version B logged {err_b} error(s)."
            ),
            evidence=self.extract_evidence(diff),
        )


class ConsoleWarningRule(ClassificationRule):
    """Fires when console warnings change."""

    rule_id = "RUNTIME-CONSOLE-WARNING"
    category = RegressionCategory.RUNTIME_ERROR
    description = "Console warning count diverged between versions."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.CONSOLE or diff.kind != DifferenceKind.CONSOLE_WARNING_CHANGED:
            return self.not_applicable()

        if config.runtime.treat_warnings_as_candidates:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=f"Console warning count changed at route '{diff.canonical_subject}'.",
                evidence=self.extract_evidence(diff),
            )

        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.UNCLASSIFIED,
            reason=f"Console warnings diverged at route '{diff.canonical_subject}' (non-breaking advisory).",
            evidence=self.extract_evidence(diff),
        )
