"""Exploration Interaction and State-Space Coverage Measurement."""

from pydantic import BaseModel, ConfigDict, Field


class CoverageMetrics(BaseModel):
    """Structured metrics summarizing interaction and state-space exploration coverage."""

    model_config = ConfigDict(extra="forbid")

    unique_routes_count: int = 0
    unique_states_count: int = 0
    unique_targets_interacted: int = 0
    transitions_attempted: int = 0
    transitions_successful: int = 0
    transitions_failed: int = 0
    candidates_skipped: int = 0
    repeated_state_visits: int = 0
    max_depth_reached: int = 0
    discovered_routes: list[str] = Field(default_factory=list)


class CoverageTracker:
    """Collects and computes exploration coverage metrics."""

    def __init__(self) -> None:
        self.unique_targets: set[str] = set()
        self.transitions_attempted: int = 0
        self.transitions_successful: int = 0
        self.transitions_failed: int = 0
        self.candidates_skipped: int = 0
        self.repeated_state_visits: int = 0
        self.max_depth_reached: int = 0

    def record_transition(
        self,
        target_identity: str,
        success: bool,
        depth: int,
        is_repeated_state: bool = False,
    ) -> None:
        self.transitions_attempted += 1
        if success:
            self.transitions_successful += 1
        else:
            self.transitions_failed += 1

        self.unique_targets.add(target_identity)
        if depth > self.max_depth_reached:
            self.max_depth_reached = depth

        if is_repeated_state:
            self.repeated_state_visits += 1

    def record_skipped_candidate(self) -> None:
        self.candidates_skipped += 1

    def build_metrics(
        self,
        unique_states_count: int,
        routes: list[str],
    ) -> CoverageMetrics:
        return CoverageMetrics(
            unique_routes_count=len(routes),
            unique_states_count=unique_states_count,
            unique_targets_interacted=len(self.unique_targets),
            transitions_attempted=self.transitions_attempted,
            transitions_successful=self.transitions_successful,
            transitions_failed=self.transitions_failed,
            candidates_skipped=self.candidates_skipped,
            repeated_state_visits=self.repeated_state_visits,
            max_depth_reached=self.max_depth_reached,
            discovered_routes=routes,
        )
