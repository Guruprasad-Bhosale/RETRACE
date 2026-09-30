"""Diagnostic and Unranked Reporting Layer for Root Cause Localization.

Renders neutral, factual summaries of localized source locations, AST symbols,
and attributed commits without arbitrary severity scores or ranking.
"""

from typing import Any

from apps.worker.rootcause.models import (
    RootCauseSuiteResult,
)


class RootCauseDiagnosticsFormatter:
    """Deterministic diagnostic log and report formatter."""

    @classmethod
    def format_suite_summary(cls, suite_result: RootCauseSuiteResult) -> str:
        """Render a comprehensive, unranked root-cause investigation report in plain text."""
        lines: list[str] = [
            "==================================================================",
            "   RETRACE ROOT CAUSE LOCALIZATION & ATTRIBUTION REPORT (PHASE 9) ",
            "==================================================================",
            f"Run A ID: {suite_result.run_a_id}",
            f"Run B ID: {suite_result.run_b_id}",
            "",
            "SUMMARY OF LOCALIZED ROOT CAUSES (UNRANKED):",
            f"  - Total Regressions Analyzed: {suite_result.summary.total_regressions_analyzed}",
            f"  - Confirmed Located:         {suite_result.summary.located_count}",
            f"  - Partially Located:         {suite_result.summary.partially_located_count}",
            f"  - Candidate Only:            {suite_result.summary.candidate_only_count}",
            f"  - Inconclusive:              {suite_result.summary.inconclusive_count}",
            f"  - Unsupported Language:      {suite_result.summary.unsupported_count}",
            "------------------------------------------------------------------",
        ]

        if not suite_result.results:
            lines.append("No regressions were evaluated.")
            lines.append("==================================================================")
            return "\n".join(lines)

        # Sort results deterministically
        sorted_results = sorted(suite_result.results, key=lambda r: r.deterministic_sort_key())

        for idx, res in enumerate(sorted_results, 1):
            lines.append(f"[{idx}] Regression Classification: {res.classification_id} ({res.category})")
            lines.append(f"    Status: {res.status.value}")
            lines.append(f"    Difference ID: {res.difference_id}")
            if res.reproduction_id:
                lines.append(f"    Reproduction ID: {res.reproduction_id}")

            if res.primary_attribution:
                attr = res.primary_attribution
                loc = attr.source_location
                sym_info = f" -> Symbol: {loc.symbol_name} ({loc.symbol_kind.value})" if loc.symbol_name and loc.symbol_kind else ""
                lines.append(f"    Source Location: {loc.file_path}:{loc.start_line}-{loc.end_line}{sym_info}")
                lines.append(f"    Relationship:    {attr.relationship_type.value}")
                lines.append(f"    Explanation:     {attr.explanation}")

                if attr.commit:
                    lines.append(f"    Attributed Commit ({attr.commit_attribution_type.value}):")
                    lines.append(f"      Hash:    {attr.commit.commit_hash[:12]}")
                    lines.append(f"      Author:  {attr.commit.author_name}")
                    lines.append(f"      Message: {attr.commit.message}")
            else:
                lines.append("    Source Location: None (Inconclusive or No Causal Diff)")

            if res.candidate_locations:
                lines.append(f"    Candidates Considered: {len(res.candidate_locations)} source location(s)")

            lines.append("------------------------------------------------------------------")

        lines.append("==================================================================")
        return "\n".join(lines)

    @classmethod
    def to_json_dict(cls, suite_result: RootCauseSuiteResult) -> dict[str, Any]:
        """Convert suite result to serializable dictionary."""
        return suite_result.model_dump(mode="json")
