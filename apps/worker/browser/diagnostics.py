"""Diagnostic Reporting and Sensor Overhead Measurement Module."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.browser.events import BrowserEvent
from packages.domain.models import Action, Observation


class SensorTimingBreakdown(BaseModel):
    """Execution latency breakdown for observation and sensor capture steps."""

    model_config = ConfigDict(extra="forbid")

    step_index: int
    action_execution_ms: float = 0.0
    stabilization_ms: float = 0.0
    dom_capture_ms: float = 0.0
    a11y_capture_ms: float = 0.0
    inventory_capture_ms: float = 0.0
    screenshot_capture_ms: float = 0.0
    artifact_persistence_ms: float = 0.0
    total_step_ms: float = 0.0


class DiagnosticSummary(BaseModel):
    """Complete structured diagnostic summary of a browser execution session."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    trajectory_id: str
    version_id: str
    analysis_id: str
    total_steps: int
    total_duration_ms: float
    actions_count: int
    failed_actions_count: int
    observations_count: int
    events_count: int
    console_errors_count: int
    network_failures_count: int
    artifacts_count: int
    step_timings: list[SensorTimingBreakdown] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosticFormatter:
    """Formats diagnostic session data for engineering inspection and reporting."""

    @staticmethod
    def generate_summary(
        analysis_id: str,
        version_id: str,
        run_id: str,
        trajectory_id: str,
        actions: list[Action],
        observations: list[Observation],
        events: list[BrowserEvent],
        timings: list[SensorTimingBreakdown],
        total_duration_ms: float,
    ) -> DiagnosticSummary:
        failed_actions = sum(1 for a in actions if not a.metadata.get("success", True))
        total_artifacts = sum(len(o.artifacts) for o in observations)
        console_errs = sum(o.state.console_errors_count for o in observations)
        net_fails = sum(o.state.network_failures_count for o in observations)

        return DiagnosticSummary(
            run_id=run_id,
            trajectory_id=trajectory_id,
            version_id=version_id,
            analysis_id=analysis_id,
            total_steps=len(observations),
            total_duration_ms=total_duration_ms,
            actions_count=len(actions),
            failed_actions_count=failed_actions,
            observations_count=len(observations),
            events_count=len(events),
            console_errors_count=console_errs,
            network_failures_count=net_fails,
            artifacts_count=total_artifacts,
            step_timings=timings,
            actions=[a.model_dump() for a in actions],
            observations=[o.model_dump() for o in observations],
            recent_events=[e.model_dump() for e in events[-50:]],
        )

    @staticmethod
    def format_text_report(summary: DiagnosticSummary) -> str:
        """Render human-readable diagnostic report for logs and debugging."""
        lines = [
            "=" * 70,
            "🔍 RETRACE BROWSER SENSOR DIAGNOSTIC REPORT",
            "=" * 70,
            f"Run ID:         {summary.run_id}",
            f"Trajectory ID:  {summary.trajectory_id}",
            f"Analysis ID:    {summary.analysis_id}",
            f"Version ID:     {summary.version_id}",
            f"Total Duration: {summary.total_duration_ms:.2f} ms",
            f"Total Steps:    {summary.total_steps}",
            f"Actions:        {summary.actions_count} (Failed: {summary.failed_actions_count})",
            f"Observations:   {summary.observations_count}",
            f"Artifacts:      {summary.artifacts_count}",
            f"Console Errors: {summary.console_errors_count}",
            f"Network Fails:  {summary.network_failures_count}",
            "-" * 70,
            "STEP TIMINGS & OVERHEAD BREAKDOWN:",
        ]

        for t in summary.step_timings:
            lines.append(
                f"  Step {t.step_index:02d}: Total={t.total_step_ms:6.1f}ms | "
                f"Action={t.action_execution_ms:5.1f}ms | Stab={t.stabilization_ms:5.1f}ms | "
                f"DOM={t.dom_capture_ms:4.1f}ms | A11y={t.a11y_capture_ms:4.1f}ms | "
                f"Inv={t.inventory_capture_ms:4.1f}ms | Img={t.screenshot_capture_ms:4.1f}ms | "
                f"Store={t.artifact_persistence_ms:4.1f}ms"
            )

        lines.append("=" * 70)
        return "\n".join(lines)
