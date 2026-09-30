"""Unit tests for evidence report generation."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reporting.engine import EvidenceReportEngine
from apps.worker.reporting.models import ReportStatus
from apps.worker.reproduction.models import (
    ActionType,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStep,
    ReproductionStrategy,
)
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    DiffHunk,
    DiffLine,
    LineChangeType,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from apps.worker.synthesis.models import (
    GeneratedTest,
    SynthesisStatus,
    TestFramework,
    TestLanguage,
    TestProvenance,
    ValidationStatus,
)


def _build_test_bundle():
    clf = RegressionClassification(
        classification_id="clf_rep_1",
        difference_id="diff_rep_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-CART-COUPON-FAILURE",
        reason="Coupon 10% discount failed to apply.",
        evidence=ClassificationEvidence(
            difference_id="diff_rep_1",
            canonical_subject="input#coupon-input",
            details={"expected_value": "$90.00", "actual_value": "$100.00", "coupon": "DISCOUNT10"},
        ),
    )

    steps = [
        ReproductionStep(step_index=0, action_type=ActionType.NAVIGATE, value="/cart"),
        ReproductionStep(step_index=1, action_type=ActionType.TYPE, stable_target_identity="#coupon-input", value="DISCOUNT10"),
        ReproductionStep(step_index=2, action_type=ActionType.CLICK, stable_target_identity="#apply-coupon-btn"),
    ]
    repro = ReproductionResult(
        reproduction_id="repro_rep_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p1", trajectory_id=uuid4(), classification_id=clf.classification_id,
            difference_id=clf.difference_id, seed_url="http://127.0.0.1:3000/cart", steps=steps, path_signature="nav->type->click",
        ),
    )

    loc = SourceLocation(file_path="src/pricing/discounts.py", start_line=12, end_line=18, symbol_name="apply_discount")
    commit = CommitMetadata(commit_hash="abc123456789", author_name="Alice", message="Refactor discount rules")
    hunk = DiffHunk(
        old_start=12,
        old_lines=5,
        new_start=12,
        new_lines=5,
        lines=[
            DiffLine(old_line_number=12, change_type=LineChangeType.LINE_DELETED, content="return total * (1 - rate)"),
            DiffLine(new_line_number=12, change_type=LineChangeType.LINE_ADDED, content="return total"),
        ],
    )
    attr = RootCauseAttribution(
        attribution_id="attr_rep_1",
        source_location=loc,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=commit,
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        diff_hunk=hunk,
        explanation="Discount multiplier removed from calculation.",
    )
    rc = RootCauseResult(
        root_cause_id="rc_rep_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    gen_test = GeneratedTest(
        test_id="test_rep_1",
        regression_id=clf.classification_id,
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Coupon Discount Regression",
        description="Verifies coupon discount",
        steps=[],
        assertions=[],
        provenance=TestProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
        status=SynthesisStatus.SYNTHESIZED,
        validation_status=ValidationStatus.STRUCTURALLY_VALIDATED,
        generated_source="import { test, expect } from '@playwright/test';",
    )

    return clf, repro, rc, gen_test


def test_generate_complete_investigation_report():
    """Verify generation of full 11-section report with markdown and JSON content."""
    clf, repro, rc, gen_test = _build_test_bundle()
    engine = EvidenceReportEngine()

    report = engine.generate_report(
        classification=clf,
        reproduction=repro,
        root_cause=rc,
        generated_test=gen_test,
        investigation_id="inv_001",
    )

    assert report.status == ReportStatus.COMPLETE
    assert len(report.sections) == 11
    assert report.sections[0].title == "1. Executive Summary"
    assert report.sections[6].title == "7. Source Localization"
    assert report.sections[7].title == "8. Commit Attribution"
    assert report.sections[8].title == "9. Evidence Chain"
    assert report.sections[9].title == "10. Generated Regression Test"
    assert report.sections[10].title == "11. Limitations & Scope Boundaries"

    # Markdown validations
    assert "# RETRACE Investigation Report:" in report.markdown_content
    assert "src/pricing/discounts.py" in report.markdown_content
    assert "abc12345" in report.markdown_content
    assert "CAUSAL_COMMIT" in report.markdown_content

    # JSON validations
    assert report.json_content["report_id"] == report.report_id
    assert len(report.json_content["sections"]) == 11
    assert report.json_content["evidence_chain"]["chain_id"] is not None
