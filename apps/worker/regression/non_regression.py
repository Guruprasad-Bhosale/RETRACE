"""Non-Regression Classification Rules.

Identifies explicitly presentational, non-actionable copy or branding modifications as non-regressions.
"""

from apps.worker.diff.models import DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class PresentationalTextRule(ClassificationRule):
    """Fires when text changes occur strictly on verified non-actionable, presentational copy."""

    rule_id = "NON-REG-PRESENTATIONAL"
    category = RegressionCategory.NON_REGRESSION
    description = "Observed copy or title text change is verified purely presentational and non-actionable."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind not in (DifferenceKind.DOM_TEXT_CHANGED, DifferenceKind.PAGE_TITLE_CHANGED):
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        details = ev.details if ev else {}

        # Only classify as NON_REGRESSION if explicitly confirmed presentational/non-actionable in evidence
        if details.get("is_presentational") or details.get("element_role") in ("heading", "paragraph", "footer", "meta"):
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.NON_REGRESSION,
                reason=f"Text modification at '{diff.canonical_subject}' is confirmed purely presentational/copy.",
                evidence=self.extract_evidence(diff),
            )

        # Otherwise do not force NON_REGRESSION; leave unclassified
        return self.not_applicable()
