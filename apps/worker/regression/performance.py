"""Performance Regression Classification Rules.

Detects performance regressions exceeding configured absolute timing increase thresholds.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class NavigationPerformanceRule(ClassificationRule):
    """Fires when navigation duration increases beyond the configured absolute threshold."""

    rule_id = "PERF-NAVIGATION-SLOWDOWN"
    category = RegressionCategory.PERFORMANCE
    description = "Navigation or transition duration exceeded absolute regression threshold."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.PERFORMANCE or diff.kind != DifferenceKind.NAVIGATION_DURATION_CHANGED:
            return self.not_applicable()

        if not config.performance.enabled:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.UNCLASSIFIED,
                reason="Performance classification policy is disabled.",
                evidence=self.extract_evidence(diff),
            )

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        delta_ms = ev.details.get("delta_ms")
        if delta_ms is None:
            # Try to calculate from before/after
            try:
                b_str = str(ev.before_value).replace("ms", "").strip()
                a_str = str(ev.after_value).replace("ms", "").strip()
                delta_ms = float(a_str) - float(b_str)
            except Exception:
                delta_ms = None

        if delta_ms is not None and delta_ms >= config.performance.navigation_delta_threshold_ms:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"Transition duration at '{diff.canonical_subject}' increased by {delta_ms:.2f} ms "
                    f"(threshold: {config.performance.navigation_delta_threshold_ms:.2f} ms)."
                ),
                evidence=self.extract_evidence(diff, {"delta_ms": delta_ms}),
            )

        return self.not_applicable()


class StabilizationPerformanceRule(ClassificationRule):
    """Fires when page stabilization duration increases beyond the threshold."""

    rule_id = "PERF-STABILIZATION-SLOWDOWN"
    category = RegressionCategory.PERFORMANCE
    description = "Page stabilization duration exceeded absolute regression threshold."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.PERFORMANCE or diff.kind != DifferenceKind.STABILIZATION_DURATION_CHANGED:
            return self.not_applicable()

        if not config.performance.enabled:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.UNCLASSIFIED,
                reason="Performance classification policy is disabled.",
                evidence=self.extract_evidence(diff),
            )

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        delta_ms = ev.details.get("delta_ms")
        if delta_ms is not None and delta_ms >= config.performance.stabilization_delta_threshold_ms:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=(
                    f"Stabilization duration at '{diff.canonical_subject}' increased by {delta_ms:.2f} ms "
                    f"(threshold: {config.performance.stabilization_delta_threshold_ms:.2f} ms)."
                ),
                evidence=self.extract_evidence(diff, {"delta_ms": delta_ms}),
            )

        return self.not_applicable()
