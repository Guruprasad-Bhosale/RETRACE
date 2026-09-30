"""Semantic Difference Diagnostic and Summary Formatter.

Formats human-readable neutral diagnostic reports and structured JSON models
without regression classification or subjective judgments.
"""

from typing import Any

from apps.worker.diff.models import SemanticDiffResult


class DiffDiagnosticsFormatter:
    """Renders human-readable summaries and structured payloads of semantic differences."""

    @staticmethod
    def format_text_summary(result: SemanticDiffResult) -> str:
        """Format a human-readable text report describing observed differences."""
        s = result.summary
        lines = [
            "=" * 70,
            "🔬 RETRACE SEMANTIC DIFFERENCE REPORT",
            "=" * 70,
            f"Run A ID:           {result.run_a_id}",
            f"Run B ID:           {result.run_b_id}",
            f"Trajectory A ID:    {result.trajectory_a_id}",
            f"Trajectory B ID:    {result.trajectory_b_id}",
            "-" * 70,
            "TOPOLOGY COMPARISON COUNTS:",
            f"  States Compared:        {s.states_compared}",
            f"  States Only in A:       {s.states_only_in_a}",
            f"  States Only in B:       {s.states_only_in_b}",
            f"  Ambiguous States:       {s.states_ambiguous}",
            f"  Actions Compared:       {s.actions_compared}",
            f"  Transitions Compared:   {s.transitions_compared}",
            f"  Transitions Only in A:  {s.transitions_only_in_a}",
            f"  Transitions Only in B:  {s.transitions_only_in_b}",
            "-" * 70,
            "SEMANTIC DIFFERENCE BREAKDOWN:",
            f"  DOM Differences:            {s.dom_differences}",
            f"  Accessibility Differences:  {s.accessibility_differences}",
            f"  Interaction Differences:    {s.interaction_differences}",
            f"  Network Differences:        {s.network_differences}",
            f"  Console Differences:        {s.console_differences}",
            f"  Performance Differences:    {s.performance_differences}",
            f"  Total Observable Diff(s):   {s.total_differences}",
            "-" * 70,
        ]

        if result.differences:
            lines.append("OBSERVED DIFFERENCES:")
            for idx, diff in enumerate(result.differences, 1):
                lines.append(f"  {idx}. [{diff.category.value}] {diff.kind.value}: {diff.description}")
        else:
            lines.append("No observable semantic differences detected between aligned topologies.")

        if result.limitations:
            lines.append("-" * 70)
            lines.append("COMPARISON LIMITATIONS:")
            for lim in result.limitations:
                lines.append(f"  • {lim}")

        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def format_json(result: SemanticDiffResult) -> dict[str, Any]:
        """Convert result model to serialized dictionary payload."""
        return result.model_dump(mode="json")
