"""Alignment Diagnostic Formatting and Reporting Module.

Renders human-readable summaries of Version A/B behavioral trajectory alignment,
divergences, and topological correspondence.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult


class AlignmentDiagnosticsFormatter:
    """Formats AlignmentResult into structured diagnostic reports and console summaries."""

    @staticmethod
    def format_text_summary(result: AlignmentResult) -> str:
        """Render human-readable diagnostic report of behavioral trajectory alignment."""
        align = result.alignment

        exact_states = sum(1 for s in align.aligned_states if s.relation == AlignmentRelation.EXACT_MATCH)
        strong_states = sum(1 for s in align.aligned_states if s.relation == AlignmentRelation.STRONG_MATCH)
        partial_states = sum(1 for s in align.aligned_states if s.relation == AlignmentRelation.PARTIAL_MATCH)

        lines = [
            "=" * 70,
            "⚖️ RETRACE BEHAVIORAL TRAJECTORY ALIGNMENT REPORT",
            "=" * 70,
            f"Run A ID:           {result.run_a_id}",
            f"Run B ID:           {result.run_b_id}",
            f"Trajectory A ID:    {result.trajectory_a_id}",
            f"Trajectory B ID:    {result.trajectory_b_id}",
            "-" * 70,
            "STATE ALIGNMENT SUMMARY:",
            f"  Total Aligned States: {len(align.aligned_states)}",
            f"    - Exact Matches:    {exact_states}",
            f"    - Strong Matches:   {strong_states}",
            f"    - Partial Matches:  {partial_states}",
            f"  Ambiguous States:     {len(align.ambiguous_states)}",
            f"  Unmatched in A:       {len(align.unmatched_a_states)}",
            f"  Unmatched in B:       {len(align.unmatched_b_states)}",
            "-" * 70,
            "TRANSITION & ROUTE SUMMARY:",
            f"  Aligned Transitions:  {len(align.aligned_transitions)}",
            f"  Unique Routes A:      {len(align.unique_routes_a)} ({', '.join(align.unique_routes_a)})",
            f"  Unique Routes B:      {len(align.unique_routes_b)} ({', '.join(align.unique_routes_b)})",
            f"  Aligned Routes Count: {align.aligned_routes_count}",
            "-" * 70,
            f"DIVERGENCES OBSERVED ({len(align.divergences)}):",
        ]

        if not align.divergences:
            lines.append("  (None observed)")
        else:
            for idx, div in enumerate(align.divergences, 1):
                lines.append(f"  [{idx}] {div.divergence_type.value}: {div.description}")

        lines.append("=" * 70)
        return "\n".join(lines)
