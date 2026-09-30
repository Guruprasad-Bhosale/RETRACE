"""Accessibility Regression Classification Rules.

Detects accessibility regressions such as stripped ARIA roles and removed accessible names,
while cautiously classifying hash-only structural changes as unclassified.
"""

from apps.worker.diff.models import DifferenceCategory, DifferenceKind, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)
from apps.worker.regression.rules import ClassificationRule


class AccessibilityRoleChangedRule(ClassificationRule):
    """Fires when an accessible role is removed or altered."""

    rule_id = "A11Y-ROLE-CHANGED"
    category = RegressionCategory.ACCESSIBILITY
    description = "Accessible element role was modified or removed."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.ACCESSIBILITY or diff.kind != DifferenceKind.A11Y_ROLE_CHANGED:
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        return RuleEvaluation(
            applicable=True,
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            reason=f"Accessible role changed at '{diff.canonical_subject}': A='{ev.before_value if ev else ''}', B='{ev.after_value if ev else ''}'.",
            evidence=self.extract_evidence(diff),
        )


class AccessibilityNameRemovedRule(ClassificationRule):
    """Fires when an accessible name or label is completely removed."""

    rule_id = "A11Y-NAME-CHANGED"
    category = RegressionCategory.ACCESSIBILITY
    description = "Accessible name or label was removed from an interactive element."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.kind not in (DifferenceKind.A11Y_NAME_CHANGED, DifferenceKind.ACTION_NAME_CHANGED):
            return self.not_applicable()

        ev = diff.evidence[0] if diff.evidence else None
        if not ev:
            return self.not_applicable()

        # Name present in A but missing / empty in B
        if ev.before_value and not ev.after_value:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                reason=f"Accessible name '{ev.before_value}' was removed for '{diff.canonical_subject}' in Version B.",
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()


class AccessibilityHashFallbackRule(ClassificationRule):
    """Fires when an accessibility difference is based purely on tree hashes without node-level evidence."""

    rule_id = "A11Y-STRUCTURE-HASH"
    category = RegressionCategory.ACCESSIBILITY
    description = "Accessibility tree hash divergence without explicit node evidence."

    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        if diff.category != DifferenceCategory.ACCESSIBILITY or diff.kind != DifferenceKind.A11Y_STRUCTURE_CHANGED:
            return self.not_applicable()

        if config.accessibility.classify_hash_only_as_unclassified:
            return RuleEvaluation(
                applicable=True,
                status=ClassificationStatus.UNCLASSIFIED,
                reason=(
                    f"Accessibility tree hash changed at '{diff.canonical_subject}', "
                    "but specific node modifications cannot be established without detailed tree evidence."
                ),
                evidence=self.extract_evidence(diff),
            )

        return self.not_applicable()
