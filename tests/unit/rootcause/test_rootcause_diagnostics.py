"""Unit tests for diagnostic reporting and unranked summary formatting."""

from uuid import uuid4

from apps.worker.rootcause.diagnostics import RootCauseDiagnosticsFormatter
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    RootCauseSuiteResult,
    RootCauseSummary,
    SourceLocation,
)


def test_diagnostics_formatter_unranked_report():
    """Verify diagnostic report is neutral, unranked, and contains no severity scores."""
    loc = SourceLocation(
        file_path="static/cart.html",
        symbol_name="<a id='checkout'>",
        start_line=20,
        end_line=22,
    )
    commit = CommitMetadata(
        commit_hash="4b82e1" + "0" * 34,
        author_name="Bob",
        message="fix router path",
    )
    attr = RootCauseAttribution(
        attribution_id="attr-01",
        source_location=loc,
        relationship_type=AttributionRelationshipType.AFFECTED_ROUTE,
        commit=commit,
        commit_attribution_type=CommitAttributionType.INTRODUCING_COMMIT,
        explanation="Checkout route changed to 404 target",
        evidence=[],
    )
    prov = RootCauseProvenance(classification_id="class-01", difference_id="diff-01")

    res = RootCauseResult(
        root_cause_id="rc-01",
        classification_id="class-01",
        difference_id="diff-01",
        category="NAVIGATION",
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=prov,
    )

    suite = RootCauseSuiteResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        results=[res],
        summary=RootCauseSummary(
            total_regressions_analyzed=1,
            located_count=1,
        ),
    )

    text = RootCauseDiagnosticsFormatter.format_suite_summary(suite)
    assert "RETRACE ROOT CAUSE LOCALIZATION & ATTRIBUTION REPORT" in text
    assert "SUMMARY OF LOCALIZED ROOT CAUSES (UNRANKED):" in text
    assert "static/cart.html:20-22" in text
    assert "fix router path" in text

    # Boundary invariants in text
    assert "severity" not in text.lower()
    assert "priority" not in text.lower()
    assert "critical" not in text.lower()
