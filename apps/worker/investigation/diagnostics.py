"""Investigation Package Diagnostics Formatter.

Formats neutral, unranked textual summaries for full investigation suite packages.
"""

from apps.worker.investigation.models import InvestigationSuiteResult


class InvestigationDiagnosticsFormatter:
    """Renders structured, unranked textual summaries for investigation suites."""

    @classmethod
    def format_suite_summary(cls, suite: InvestigationSuiteResult) -> str:
        """Format an unranked plain-text summary of investigated regressions."""
        lines = [
            "================================================================================",
            "                 RETRACE INVESTIGATION PACKAGES SUMMARY REPORT                  ",
            "================================================================================",
            f"Analysis ID: {suite.analysis_id}",
            f"Run A ID:    {suite.run_a_id}",
            f"Run B ID:    {suite.run_b_id}",
            f"Total Investigations:    {suite.summary.total_investigations}",
            f"Completed Investigations:{suite.summary.completed_count}",
            f"Partial Investigations:  {suite.summary.partial_count}",
            f"Inconclusive / Skipped:  {suite.summary.inconclusive_count}",
            "--------------------------------------------------------------------------------",
            "INVESTIGATION PACKAGES (UNRANKED):",
        ]

        if not suite.investigations:
            lines.append("  (No investigation packages assembled)")
        else:
            for idx, inv in enumerate(suite.investigations, start=1):
                clf = inv.classification
                cat_val = clf.category.value if hasattr(clf.category, "value") else str(clf.category)
                repro_val = inv.reproduction.status.value if inv.reproduction else "NOT_REPRODUCED"
                rc_val = inv.root_cause.status.value if inv.root_cause else "NOT_LOCALIZED"
                test_val = inv.generated_test.status.value if inv.generated_test else "NOT_GENERATED"

                lines.append(f"  {idx}. Investigation [{inv.investigation_id}]")
                lines.append(f"     Category:       {cat_val} (Rule: {clf.rule_id})")
                lines.append(f"     Overall Status: {inv.status.value}")
                lines.append(f"     Reproduction:   {repro_val}")
                lines.append(f"     Root Cause:     {rc_val}")
                lines.append(f"     Test Artifact:  {test_val}")
                lines.append(f"     Artifacts Count:{len(inv.artifacts)}")
                lines.append("")

        lines.append("================================================================================")
        return "\n".join(lines)
