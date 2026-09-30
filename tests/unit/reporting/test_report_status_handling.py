"""Unit tests for report root-cause status preservation and negative upgrade prevention."""

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reporting.engine import EvidenceReportEngine
from apps.worker.rootcause.models import (
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)


def test_candidate_only_status_never_upgraded_in_report():
    """Verify CANDIDATE_ONLY status is strictly preserved and flagged in report."""
    clf = RegressionClassification(
        classification_id="clf_cand_1",
        difference_id="diff_cand_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="RULE-PERF-LATENCY-SPIKE",
        reason="Latency spike.",
        evidence=ClassificationEvidence(difference_id="diff_cand_1"),
    )
    rc = RootCauseResult(
        root_cause_id="rc_cand_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.CANDIDATE_ONLY,
        candidate_locations=[SourceLocation(file_path="src/heavy_job.py", start_line=10, end_line=20)],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    engine = EvidenceReportEngine()
    report = engine.generate_report(classification=clf, root_cause=rc)

    # Section 7 source localization
    sec_7 = report.sections[6]
    assert "CANDIDATE_ONLY" in sec_7.content_markdown
    assert "does not conclusively establish causality" in sec_7.content_markdown
    assert "CONFIRMED" not in sec_7.content_markdown


def test_inconclusive_status_never_upgraded_in_report():
    """Verify INCONCLUSIVE status is preserved without synthetic claims."""
    clf = RegressionClassification(
        classification_id="clf_inc_1",
        difference_id="diff_inc_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.UI_BEHAVIOR,
        rule_id="RULE-UI-MISMATCH",
        reason="UI discrepancy.",
        evidence=ClassificationEvidence(difference_id="diff_inc_1"),
    )
    rc = RootCauseResult(
        root_cause_id="rc_inc_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.INCONCLUSIVE,
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    engine = EvidenceReportEngine()
    report = engine.generate_report(classification=clf, root_cause=rc)

    sec_7 = report.sections[6]
    assert "INCONCLUSIVE" in sec_7.content_markdown
    assert "Source diff analysis was inconclusive" in sec_7.content_markdown
