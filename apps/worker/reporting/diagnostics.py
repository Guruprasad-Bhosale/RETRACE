"""Evidence Reporting Diagnostics Formatter.

Formats neutral, unranked textual diagnostics for investigation report suites.
"""

from apps.worker.reporting.models import ReportSuiteResult


class ReportingDiagnosticsFormatter:
    """Renders structured, unranked textual diagnostics for investigation report suites."""

    @classmethod
    def format_suite_summary(cls, suite: ReportSuiteResult) -> str:
        """Format an unranked plain-text summary of generated reports."""
        lines = [
            "================================================================================",
            "              RETRACE EVIDENCE INVESTIGATION REPORTS DIAGNOSTICS                ",
            "================================================================================",
            f"Run A ID: {suite.run_a_id}",
            f"Run B ID: {suite.run_b_id}",
            f"Total Reports Generated:     {suite.summary.total_reports_generated}",
            f"Complete Reports:            {suite.summary.complete_count}",
            f"Partial Reports:             {suite.summary.partial_count}",
            f"Insufficient Evidence:       {suite.summary.insufficient_evidence_count}",
            "--------------------------------------------------------------------------------",
            "INVESTIGATION REPORTS (UNRANKED):",
        ]

        if not suite.reports:
            lines.append("  (No reports generated)")
        else:
            for idx, r in enumerate(suite.reports, start=1):
                lines.append(f"  {idx}. Report [{r.report_id}]")
                lines.append(f"     Title:          {r.title}")
                lines.append(f"     Status:         {r.status.value}")
                lines.append(f"     Summary:        {r.summary}")
                lines.append(f"     Sections:       {len(r.sections)}")
                lines.append(f"     Evidence Nodes: {len(r.evidence_chain.nodes)}")
                lines.append("")

        lines.append("================================================================================")
        return "\n".join(lines)
