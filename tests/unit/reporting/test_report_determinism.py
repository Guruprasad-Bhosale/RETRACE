"""Unit tests for report determinism."""

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reporting.engine import EvidenceReportEngine


def test_report_generation_is_strictly_deterministic():
    """Verify identical inputs produce identical report IDs, JSON, and Markdown bytes."""
    clf = RegressionClassification(
        classification_id="clf_det_rep_1",
        difference_id="diff_det_rep_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.API_CONTRACT,
        rule_id="RULE-API-PAYLOAD-CHANGED",
        reason="Field missing from response.",
        evidence=ClassificationEvidence(
            difference_id="diff_det_rep_1",
            details={"endpoint": "/api/users", "status_a": 200, "status_b": 200},
        ),
    )

    engine1 = EvidenceReportEngine()
    engine2 = EvidenceReportEngine()

    rep1 = engine1.generate_report(classification=clf)
    rep2 = engine2.generate_report(classification=clf)

    assert rep1.report_id == rep2.report_id
    assert rep1.markdown_content == rep2.markdown_content
    assert rep1.json_content == rep2.json_content
