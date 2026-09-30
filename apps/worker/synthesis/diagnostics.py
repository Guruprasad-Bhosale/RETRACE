"""Test Synthesis Diagnostics Formatter.

Formats neutral, unranked diagnostic summary reports of synthesized test suites.
"""

from apps.worker.synthesis.models import SynthesisSuiteResult


class SynthesisDiagnosticsFormatter:
    """Renders structured, unranked textual diagnostics for test synthesis."""

    @classmethod
    def format_suite_summary(cls, suite: SynthesisSuiteResult) -> str:
        """Format an unranked plain-text summary of synthesized tests."""
        lines = [
            "================================================================================",
            "                RETRACE TEST SYNTHESIS DIAGNOSTICS REPORT                       ",
            "================================================================================",
            f"Run A ID: {suite.run_a_id}",
            f"Run B ID: {suite.run_b_id}",
            f"Total Regressions Analyzed: {suite.summary.total_regressions_analyzed}",
            f"Synthesized Tests:          {suite.summary.synthesized_count}",
            f"Partially Synthesized:      {suite.summary.partially_synthesized_count}",
            f"Incomplete / Skipped:       {suite.summary.incomplete_count}",
            f"Structurally Validated:     {suite.summary.structurally_validated_count}",
            "--------------------------------------------------------------------------------",
            "SYNTHESIZED TEST ARTIFACTS (UNRANKED):",
        ]

        if not suite.tests:
            lines.append("  (No test artifacts synthesized)")
        else:
            for idx, t in enumerate(suite.tests, start=1):
                lines.append(f"  {idx}. Test [{t.test_id}]")
                lines.append(f"     Title:             {t.title}")
                lines.append(f"     Status:            {t.status.value}")
                lines.append(f"     Validation:        {t.validation_status.value}")
                lines.append(f"     Framework/Lang:    {t.framework.value} ({t.language.value})")
                lines.append(f"     Steps:             {len(t.steps)}")
                lines.append(f"     Assertions:        {len(t.assertions)}")
                if t.provenance.source_locations:
                    lines.append(f"     Localized Source:  {', '.join(t.provenance.source_locations)}")
                if t.provenance.commit_hashes:
                    lines.append(f"     Attributed Commit: {', '.join(t.provenance.commit_hashes)}")
                if t.validation_notes:
                    lines.append(f"     Validation Notes:  {'; '.join(t.validation_notes)}")
                lines.append("")

        lines.append("================================================================================")
        return "\n".join(lines)
