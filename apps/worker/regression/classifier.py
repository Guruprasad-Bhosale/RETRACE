"""Regression Classifier Module.

Orchestrates semantic difference analysis through deterministic rule evaluation.
"""

from apps.worker.diff.models import SemanticDiffResult
from apps.worker.regression.config import RegressionConfig
from apps.worker.regression.errors import InvalidSemanticDiffError
from apps.worker.regression.models import (
    ClassificationStatus,
    ClassificationSummary,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.regression.rule_engine import RuleEngine


class RegressionClassifier:
    """Consumes SemanticDiffResult and classifies differences into deterministic regression candidates."""

    def __init__(self, config: RegressionConfig | None = None) -> None:
        self.config = config or RegressionConfig()
        self.rule_engine = RuleEngine()

    def classify(self, diff_result: SemanticDiffResult) -> RegressionClassificationResult:
        """Execute deterministic classification over all semantic differences in the result."""
        if not diff_result or not isinstance(diff_result.differences, list):
            raise InvalidSemanticDiffError("SemanticDiffResult must contain a valid list of differences.")

        raw_classifications: list[RegressionClassification] = []
        seen_ids: set[str] = set()

        for diff in diff_result.differences:
            classifications = self.rule_engine.evaluate_difference(diff, self.config)
            for c in classifications:
                if c.classification_id not in seen_ids:
                    seen_ids.add(c.classification_id)
                    raw_classifications.append(c)

        # Sort deterministically by stable key (excluding timestamps)
        sorted_classifications = sorted(
            raw_classifications,
            key=lambda c: c.deterministic_sort_key(),
        )

        # Compute summary statistics
        reg_candidates = sum(1 for c in sorted_classifications if c.status == ClassificationStatus.REGRESSION_CANDIDATE)
        non_reg = sum(1 for c in sorted_classifications if c.status == ClassificationStatus.NON_REGRESSION)
        unclass = sum(1 for c in sorted_classifications if c.status == ClassificationStatus.UNCLASSIFIED)

        by_cat: dict[RegressionCategory, int] = {}
        for c in sorted_classifications:
            if c.status == ClassificationStatus.REGRESSION_CANDIDATE:
                by_cat[c.category] = by_cat.get(c.category, 0) + 1

        summary = ClassificationSummary(
            total_differences_analyzed=len(diff_result.differences),
            regression_candidates=reg_candidates,
            non_regressions=non_reg,
            unclassified=unclass,
            candidates_by_category=by_cat,
        )

        return RegressionClassificationResult(
            run_a_id=diff_result.run_a_id,
            run_b_id=diff_result.run_b_id,
            trajectory_a_id=diff_result.trajectory_a_id,
            trajectory_b_id=diff_result.trajectory_b_id,
            classifications=sorted_classifications,
            summary=summary,
            metadata={"total_classifications": len(sorted_classifications)},
        )
