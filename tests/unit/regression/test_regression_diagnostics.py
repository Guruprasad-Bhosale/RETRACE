"""Unit tests for Regression Diagnostics Formatter."""

from uuid import uuid4

from apps.worker.regression.diagnostics import RegressionDiagnosticsFormatter
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    ClassificationSummary,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)


def test_diagnostics_formatting_without_rankings():
    c = RegressionClassification(
        classification_id="cid_abc123",
        difference_id="diff_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="HTTP status degraded from 200 to 500 at '/checkout'.",
        evidence=ClassificationEvidence(difference_id="diff_1", canonical_subject="/checkout"),
    )

    summary = ClassificationSummary(
        total_differences_analyzed=5,
        regression_candidates=1,
        non_regressions=1,
        unclassified=3,
        candidates_by_category={RegressionCategory.FUNCTIONAL: 1},
    )

    result = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[c],
        summary=summary,
    )

    text = RegressionDiagnosticsFormatter.format_text_summary(result)
    assert "RETRACE REGRESSION CLASSIFICATION REPORT" in text
    assert "Total Differences Analyzed: 5" in text
    assert "Regression Candidates:      1" in text
    assert "FUNC-HTTP-STATUS-ERROR" in text

    # Assert no ranking or severity vocabulary
    assert "most severe" not in text.lower()
    assert "top regression" not in text.lower()
    assert "critical" not in text.lower()

    json_dict = RegressionDiagnosticsFormatter.format_json(result)
    assert json_dict["summary"]["regression_candidates"] == 1
    assert len(json_dict["classifications"]) == 1
