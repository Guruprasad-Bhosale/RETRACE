"""Semantic Difference Engine Core Orchestrator.

Coordinates route, state, action, transition, network, console, accessibility,
interaction, and performance diff analyzers into a unified SemanticDiffResult.
"""

from typing import Any

from apps.worker.alignment.models import AlignmentResult
from apps.worker.diff.accessibility_diff import AccessibilityDiffer
from apps.worker.diff.action_diff import ActionDiffer
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.console_diff import ConsoleDiffer
from apps.worker.diff.errors import IncompatibleAlignmentError
from apps.worker.diff.interaction_diff import InteractionDiffer
from apps.worker.diff.models import (
    DifferenceCategory,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
)
from apps.worker.diff.network_diff import NetworkDiffer
from apps.worker.diff.performance_diff import PerformanceDiffer
from apps.worker.diff.route_diff import RouteDiffer
from apps.worker.diff.state_diff import StateDiffer
from apps.worker.diff.transition_diff import TransitionDiffer


class SemanticDiffEngine:
    """Consumes Phase 5 AlignmentResult and extracts deterministic semantic differences."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()
        self.route_differ = RouteDiffer(self.config)
        self.state_differ = StateDiffer(self.config)
        self.action_differ = ActionDiffer(self.config)
        self.transition_differ = TransitionDiffer(self.config)
        self.network_differ = NetworkDiffer(self.config)
        self.console_differ = ConsoleDiffer(self.config)
        self.a11y_differ = AccessibilityDiffer(self.config)
        self.interaction_differ = InteractionDiffer(self.config)
        self.performance_differ = PerformanceDiffer(self.config)

    def _deduplicate_and_merge_differences(
        self,
        raw_diffs: list[SemanticDifference],
    ) -> list[SemanticDifference]:
        """Merge differences sharing identical diff_id by unifying their evidence lineage."""
        merged_by_id: dict[str, SemanticDifference] = {}

        for diff in raw_diffs:
            if diff.diff_id not in merged_by_id:
                # Shallow copy diff with a new list of evidence
                merged_by_id[diff.diff_id] = diff.model_copy(
                    update={"evidence": list(diff.evidence)}
                )
            else:
                existing = merged_by_id[diff.diff_id]
                # Merge evidence without duplicate entries
                existing_subjects = {
                    (e.canonical_subject, str(e.observation_a_id), str(e.observation_b_id))
                    for e in existing.evidence
                }
                for ev in diff.evidence:
                    key = (ev.canonical_subject, str(ev.observation_a_id), str(ev.observation_b_id))
                    if key not in existing_subjects:
                        existing.evidence.append(ev)
                        existing_subjects.add(key)

        # Sort deterministically using stable structural sort key (excluding timestamps)
        return sorted(merged_by_id.values(), key=lambda d: d.deterministic_sort_key())

    def _compute_summary(
        self,
        alignment_result: AlignmentResult,
        differences: list[SemanticDifference],
    ) -> SemanticDiffSummary:
        """Compute statistical counters over compared topologies and detected difference categories."""
        align = alignment_result.alignment

        cat_counts: dict[DifferenceCategory, int] = {}
        for d in differences:
            cat_counts[d.category] = cat_counts.get(d.category, 0) + 1

        return SemanticDiffSummary(
            states_compared=len(align.aligned_states),
            states_only_in_a=len(align.unmatched_a_states),
            states_only_in_b=len(align.unmatched_b_states),
            states_ambiguous=len(align.ambiguous_states),
            actions_compared=sum(1 for ta in align.aligned_transitions if ta.action_alignment),
            transitions_compared=len(align.aligned_transitions),
            transitions_only_in_a=len(align.unmatched_a_transitions),
            transitions_only_in_b=len(align.unmatched_b_transitions),
            routes_compared=align.aligned_routes_count + len(align.unique_routes_a) + len(align.unique_routes_b),
            dom_differences=cat_counts.get(DifferenceCategory.DOM, 0),
            accessibility_differences=cat_counts.get(DifferenceCategory.ACCESSIBILITY, 0),
            interaction_differences=cat_counts.get(DifferenceCategory.INTERACTION, 0),
            network_differences=cat_counts.get(DifferenceCategory.NETWORK, 0),
            console_differences=cat_counts.get(DifferenceCategory.CONSOLE, 0),
            performance_differences=cat_counts.get(DifferenceCategory.PERFORMANCE, 0),
            total_differences=len(differences),
        )

    def compare(
        self,
        alignment_result: AlignmentResult,
        evidence_resolver: Any | None = None,
    ) -> SemanticDiffResult:
        """Execute all sub-differs and assemble a deterministic SemanticDiffResult.

        Inputs are treated as strictly immutable.
        """
        if not alignment_result or not alignment_result.alignment:
            raise IncompatibleAlignmentError("AlignmentResult must contain valid alignment topology.")

        raw_diffs: list[SemanticDifference] = []

        # Run all specialized diff engines
        raw_diffs.extend(self.route_differ.diff(alignment_result))
        raw_diffs.extend(self.state_differ.diff(alignment_result))
        raw_diffs.extend(self.action_differ.diff(alignment_result))
        raw_diffs.extend(self.transition_differ.diff(alignment_result))
        raw_diffs.extend(self.network_differ.diff(alignment_result))
        raw_diffs.extend(self.console_differ.diff(alignment_result))
        raw_diffs.extend(self.a11y_differ.diff(alignment_result))
        raw_diffs.extend(self.interaction_differ.diff(alignment_result))
        raw_diffs.extend(self.performance_differ.diff(alignment_result))

        # Deduplicate & sort deterministically
        differences = self._deduplicate_and_merge_differences(raw_diffs)

        # Build summary and statistics
        summary = self._compute_summary(alignment_result, differences)
        comparison_stats = {
            "total_differences": summary.total_differences,
            "dom_differences": summary.dom_differences,
            "a11y_differences": summary.accessibility_differences,
            "network_differences": summary.network_differences,
            "console_differences": summary.console_differences,
            "performance_differences": summary.performance_differences,
            "interaction_differences": summary.interaction_differences,
        }

        limitations: list[str] = []
        align = alignment_result.alignment
        if align.ambiguous_states:
            limitations.append(
                f"{len(align.ambiguous_states)} state comparison(s) had ambiguous structural candidates."
            )

        return SemanticDiffResult(
            run_a_id=alignment_result.run_a_id,
            run_b_id=alignment_result.run_b_id,
            trajectory_a_id=alignment_result.trajectory_a_id,
            trajectory_b_id=alignment_result.trajectory_b_id,
            differences=differences,
            summary=summary,
            comparison_statistics=comparison_stats,
            limitations=limitations,
        )
