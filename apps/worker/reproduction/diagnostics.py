"""Diagnostic Reporting and Terminal Formatting for Reproduction Results."""

import json
from typing import Any

from apps.worker.reproduction.models import (
    ReproductionResult,
    ReproductionStatus,
    ReproductionSuiteResult,
)


class ReproductionDiagnosticsFormatter:
    """Renders structured, unranked reproduction reports and diagnostics."""

    @staticmethod
    def format_result_summary(result: ReproductionResult) -> str:
        """Format a single ReproductionResult into a clean terminal report."""
        status_icon = "✅" if result.status == ReproductionStatus.REPRODUCED else "❌"
        lines = [
            f"{status_icon} REPRODUCTION [{result.status.value}] — ID: {result.reproduction_id}",
            f"   Classification ID:  {result.classification_id}",
            f"   Rule ID:            {result.rule_id} ({result.category})",
            f"   Strategy:           {result.strategy.value}",
            f"   Path Steps:         {len(result.path.steps)} (Signature: {result.path.path_signature})",
            f"   Total Duration:     {result.total_duration_ms:.2f}ms",
            f"   Attempts Count:     {len(result.attempts)}",
        ]

        if result.final_verification:
            v = result.final_verification
            lines.append(f"   Match Status:       {v.match_status.value} (Observed Match: {v.observed_match})")
            if v.matched_evidence:
                lines.append(f"   Matched Evidence:   {'; '.join(v.matched_evidence)}")
            if v.mismatched_evidence:
                lines.append(f"   Mismatched Evidence:{'; '.join(v.mismatched_evidence)}")

        return "\n".join(lines)

    @classmethod
    def format_suite_summary(cls, suite: ReproductionSuiteResult) -> str:
        """Format a complete ReproductionSuiteResult into an unranked summary report."""
        summary = suite.summary
        lines = [
            "=" * 75,
            "🔬 RETRACE AUTONOMOUS REGRESSION REPRODUCTION REPORT",
            "=" * 75,
            f"Run A ID:         {suite.run_a_id}",
            f"Run B ID:         {suite.run_b_id}",
            f"Trajectory A ID:  {suite.trajectory_a_id}",
            f"Trajectory B ID:  {suite.trajectory_b_id}",
            "-" * 75,
            "REPRODUCTION SUMMARY (UNRANKED):",
            f"  Total Attempted:  {summary.total_reproductions_attempted}",
            f"  Reproduced:       {summary.reproduced}",
            f"  Not Reproduced:   {summary.not_reproduced}",
            f"  Inconclusive:     {summary.inconclusive}",
            f"  Blocked (Safety): {summary.blocked}",
            f"  Failed (Exec):    {summary.failed}",
            "-" * 75,
            "INDIVIDUAL REPRODUCTIONS:",
        ]

        # Sorted strictly by deterministic sort key
        sorted_results = sorted(suite.results, key=lambda r: r.deterministic_sort_key())
        for res in sorted_results:
            lines.append(cls.format_result_summary(res))
            lines.append("")

        lines.append("=" * 75)
        return "\n".join(lines)

    @staticmethod
    def to_json_dict(suite: ReproductionSuiteResult) -> dict[str, Any]:
        """Convert suite result to standard JSON dictionary."""
        return json.loads(suite.model_dump_json())
