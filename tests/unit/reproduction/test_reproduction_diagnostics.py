"""Unit Tests for Reproduction Diagnostics Formatting."""

from uuid import uuid4

from apps.worker.reproduction.diagnostics import ReproductionDiagnosticsFormatter
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
    ReproductionSuiteResult,
    ReproductionSummary,
    ReproductionVerification,
)


def test_format_result_and_suite_summary():
    """Verify diagnostic text and JSON formatting for single result and suite."""
    path = ReproductionPath(
        path_id="p1",
        trajectory_id=uuid4(),
        classification_id="class-123",
        difference_id="diff-456",
        seed_url="http://localhost:3000/",
        path_signature="sig-123",
    )

    verif = ReproductionVerification(
        expected_difference_id="diff-456",
        expected_classification_id="class-123",
        expected_rule_id="FUNC-HTTP-STATUS-ERROR",
        expected_category="FUNCTIONAL",
        match_status=MatchStatus.FULL_MATCH,
        observed_match=True,
        matched_evidence=["Target returned 500 error."],
    )

    res = ReproductionResult(
        reproduction_id="rep-123",
        classification_id="class-123",
        difference_id="diff-456",
        rule_id="FUNC-HTTP-STATUS-ERROR",
        category="FUNCTIONAL",
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=path,
        final_verification=verif,
        total_duration_ms=450.0,
    )

    formatted_single = ReproductionDiagnosticsFormatter.format_result_summary(res)
    assert "REPRODUCED" in formatted_single
    assert "FUNC-HTTP-STATUS-ERROR" in formatted_single
    assert "Target returned 500 error." in formatted_single

    suite = ReproductionSuiteResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        results=[res],
        summary=ReproductionSummary(
            total_reproductions_attempted=1,
            reproduced=1,
            not_reproduced=0,
        ),
    )

    formatted_suite = ReproductionDiagnosticsFormatter.format_suite_summary(suite)
    assert "RETRACE AUTONOMOUS REGRESSION REPRODUCTION REPORT" in formatted_suite
    assert "Total Attempted:  1" in formatted_suite
    assert "Reproduced:       1" in formatted_suite

    json_dict = ReproductionDiagnosticsFormatter.to_json_dict(suite)
    assert json_dict["summary"]["reproduced"] == 1
    assert len(json_dict["results"]) == 1
