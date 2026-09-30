"""Base Classification Rule Definition and Rule Protocol.

Defines the core interface for deterministic regression classification rules.
"""

from abc import ABC, abstractmethod
from typing import Any

from apps.worker.diff.models import DifferenceEvidence, SemanticDifference
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RuleEvaluation,
)


class ClassificationRule(ABC):
    """Abstract base class for deterministic, evidence-backed regression classification rules."""

    rule_id: str
    category: RegressionCategory
    description: str

    @abstractmethod
    def evaluate(
        self,
        diff: SemanticDifference,
        config: RegressionConfig,
    ) -> RuleEvaluation:
        """Evaluate a semantic difference against this deterministic rule.

        Returns RuleEvaluation with applicable=True if the rule fires, or applicable=False if not applicable.
        """
        pass

    @staticmethod
    def extract_evidence(
        diff: SemanticDifference,
        details: dict[str, Any] | None = None,
    ) -> ClassificationEvidence:
        """Extract authoritative provenance and artifact references from a SemanticDifference."""
        ev: DifferenceEvidence | None = diff.evidence[0] if diff.evidence else None
        merged_details = dict(ev.details) if ev else {}
        if details:
            merged_details.update(details)

        return ClassificationEvidence(
            difference_id=diff.diff_id,
            canonical_subject=diff.canonical_subject,
            observation_a_id=ev.observation_a_id if ev else None,
            observation_b_id=ev.observation_b_id if ev else None,
            state_a_id=ev.state_a_id if ev else None,
            state_b_id=ev.state_b_id if ev else None,
            action_a_id=ev.action_a_id if ev else None,
            action_b_id=ev.action_b_id if ev else None,
            transition_a_id=ev.transition_a_id if ev else None,
            transition_b_id=ev.transition_b_id if ev else None,
            artifact_references=list(ev.artifact_references) if ev else [],
            details=merged_details,
        )

    def not_applicable(self) -> RuleEvaluation:
        """Helper to indicate that this rule does not apply to the given difference."""
        return RuleEvaluation(
            applicable=False,
            status=ClassificationStatus.UNCLASSIFIED,
            reason="Rule not applicable.",
            evidence=None,
        )
