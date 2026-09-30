"""Exploration Diagnostic Reporting and Result Model."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.exploration.coverage import CoverageMetrics
from packages.domain.models import ArtifactReference


class ExplorationResult(BaseModel):
    """Structured diagnostic summary of an autonomous exploration execution."""

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    trajectory_id: UUID
    seed_url: str
    total_steps: int
    states_discovered: int
    transitions_count: int
    successful_transitions: int
    failed_transitions: int
    skipped_candidates: int
    unique_routes: list[str] = Field(default_factory=list)
    termination_reason: str
    elapsed_time_sec: float
    coverage: CoverageMetrics
    state_graph_nodes: list[dict[str, Any]] = Field(default_factory=list)
    state_graph_edges: list[dict[str, Any]] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)


class ExplorationDiagnosticsFormatter:
    """Renders human-readable exploration summaries for logs and debugging."""

    @staticmethod
    def format_text_summary(result: ExplorationResult) -> str:
        lines = [
            "=" * 70,
            "🗺️ RETRACE AUTONOMOUS EXPLORATION SUMMARY",
            "=" * 70,
            f"Run ID:             {result.run_id}",
            f"Trajectory ID:      {result.trajectory_id}",
            f"Seed URL:           {result.seed_url}",
            f"Total Steps:        {result.total_steps}",
            f"Elapsed Time:       {result.elapsed_time_sec:.2f}s",
            f"Termination Reason: {result.termination_reason}",
            "-" * 70,
            "COVERAGE & STATE METRICS:",
            f"  Unique States:        {result.states_discovered}",
            f"  Discovered Routes:    {len(result.unique_routes)} ({', '.join(result.unique_routes)})",
            f"  Transitions Attempted:{result.transitions_count} (Success: {result.successful_transitions}, Fail: {result.failed_transitions})",
            f"  Candidates Skipped:   {result.skipped_candidates}",
            f"  Max Depth Reached:    {result.coverage.max_depth_reached}",
            f"  Artifacts Persisted:  {len(result.artifact_references)}",
            "=" * 70,
        ]
        return "\n".join(lines)
