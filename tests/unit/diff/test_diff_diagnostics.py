"""Unit tests for Semantic Diff Diagnostics Formatter."""

from uuid import uuid4

from apps.worker.diff.diagnostics import DiffDiagnosticsFormatter
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
)


def test_diagnostics_formatting():
    diff = SemanticDifference(
        diff_id="d1234567890abcde",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="HTTP status changed from 200 to 404 at route '/checkout'.",
        evidence=[
            DifferenceEvidence(
                canonical_subject="state:/checkout",
                before_value=200,
                after_value=404,
            )
        ],
    )

    summary = SemanticDiffSummary(
        states_compared=5,
        routes_compared=4,
        dom_differences=0,
        network_differences=0,
        console_differences=0,
        performance_differences=0,
        total_differences=1,
    )

    result = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff],
        summary=summary,
        comparison_statistics={"total_differences": 1},
        limitations=["None observed."],
    )

    text = DiffDiagnosticsFormatter.format_text_summary(result)
    assert "RETRACE SEMANTIC DIFFERENCE REPORT" in text
    assert "States Compared:        5" in text
    assert "HTTP_STATUS_CHANGED" in text
    assert "None observed." in text

    json_dict = DiffDiagnosticsFormatter.format_json(result)
    assert json_dict["summary"]["total_differences"] == 1
    assert len(json_dict["differences"]) == 1
