"""Unit tests for Ambiguity and Insufficient Evidence Handling."""

from uuid import uuid4

from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
)
from apps.worker.regression.classifier import RegressionClassifier
from apps.worker.regression.models import ClassificationStatus, RegressionCategory


def test_ambiguous_semantic_difference_remains_unclassified():
    classifier = RegressionClassifier()

    diff_ambig = SemanticDifference(
        diff_id="d_ambig_1",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.STATE_AMBIGUOUS,
        canonical_subject="state:ambig_target",
        comparison_status=ComparisonStatus.NOT_COMPARABLE,
        description="State correspondence is ambiguous between 2 candidates",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:ambig_target",
                comparison_completeness="ambiguous",
            )
        ],
    )

    diff_res = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff_ambig],
        summary=SemanticDiffSummary(total_differences=1),
    )

    class_res = classifier.classify(diff_res)
    assert len(class_res.classifications) == 1
    c = class_res.classifications[0]

    assert c.status == ClassificationStatus.UNCLASSIFIED
    assert c.category == RegressionCategory.UNKNOWN
    assert c.rule_id == "AMBIG-INSUFFICIENT-EVIDENCE"
    assert "ambiguous" in c.reason
