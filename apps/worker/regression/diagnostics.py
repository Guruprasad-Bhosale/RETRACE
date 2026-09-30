"""Regression Diagnostic and Summary Formatter.

Formats human-readable neutral diagnostic reports and structured JSON payloads
without severity rankings, bug scores, or priority ordering.
"""

from typing import Any

from apps.worker.regression.models import ClassificationStatus, RegressionClassificationResult


class RegressionDiagnosticsFormatter:
    """Renders human-readable summaries and structured outputs of regression classifications."""

    @staticmethod
    def format_text_summary(result: RegressionClassificationResult) -> str:
        """Format an unranked, neutral summary of classified regression candidates."""
        s = result.summary
        lines = [
            "=" * 70,
            "📋 RETRACE REGRESSION CLASSIFICATION REPORT",
            "=" * 70,
            f"Run A ID:           {result.run_a_id}",
            f"Run B ID:           {result.run_b_id}",
            f"Trajectory A ID:    {result.trajectory_a_id}",
            f"Trajectory B ID:    {result.trajectory_b_id}",
            "-" * 70,
            "CLASSIFICATION SUMMARY COUNTS:",
            f"  Total Differences Analyzed: {s.total_differences_analyzed}",
            f"  Regression Candidates:      {s.regression_candidates}",
            f"  Non-Regressions:            {s.non_regressions}",
            f"  Unclassified Differences:   {s.unclassified}",
            "-" * 70,
            "CANDIDATES BY CATEGORY:",
        ]

        if s.candidates_by_category:
            for cat, count in sorted(s.candidates_by_category.items(), key=lambda x: x[0].value):
                lines.append(f"  • {cat.value:<20}: {count}")
        else:
            lines.append("  (No regression candidates identified)")

        lines.append("-" * 70)

        candidates = [c for c in result.classifications if c.status == ClassificationStatus.REGRESSION_CANDIDATE]
        if candidates:
            lines.append("REGRESSION CANDIDATES:")
            for idx, c in enumerate(candidates, 1):
                lines.append(f"  {idx}. [{c.category.value}] Rule {c.rule_id}: {c.reason}")
        else:
            lines.append("No regression candidates identified.")

        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def format_json(result: RegressionClassificationResult) -> dict[str, Any]:
        """Convert classification result model to serialized dictionary payload."""
        return result.model_dump(mode="json")
