"""RETRACE Autonomous Exploration Engine Configuration."""

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field


class ExplorationConfig(BaseModel):
    """Strongly typed configuration for deterministic state-space exploration."""

    model_config = ConfigDict(extra="forbid")

    seed_url: str
    max_steps: int = Field(default=50, ge=1, le=1000, description="Hard cap on total browser actions")
    max_depth: int = Field(default=10, ge=1, le=100, description="Maximum BFS exploration depth from seed")
    max_actions_per_state: int = Field(
        default=8, ge=1, le=50, description="Maximum candidate actions to evaluate per unique state"
    )
    max_repeated_state_visits: int = Field(
        default=3, ge=1, le=20, description="Maximum times a state identity can be revisited for exploration"
    )
    max_same_action_retries: int = Field(default=2, ge=0, le=5)
    max_action_failures: int = Field(default=5, ge=1, le=50)
    max_navigation_failures: int = Field(default=3, ge=1, le=20)
    exploration_timeout_sec: float = Field(default=120.0, ge=5.0, le=1800.0)
    action_timeout_ms: float = Field(default=8000.0, ge=500.0, le=60000.0)
    allowed_domains: list[str] = Field(default_factory=list)
    allowed_url_schemes: list[str] = Field(default_factory=lambda: ["http", "https"])
    allow_destructive_actions: bool = False
    # V1 uses deterministic breadth-first search (BFS). Alternative traversals are deferred.
    traversal_strategy: str = "bfs"
    synthetic_inputs: dict[str, str] = Field(
        default_factory=lambda: {
            "text": "retrace-test",
            "email": "retrace@example.invalid",
            "number": "1",
            "search": "test",
            "tel": "555-0199",
            "url": "https://example.invalid",
            "date": "2026-01-01",
        }
    )

    def get_effective_allowed_domains(self) -> set[str]:
        """Compute set of allowed domains, defaulting to seed URL domain if empty."""
        domains = {d.lower() for d in self.allowed_domains}
        if self.seed_url:
            parsed = urlparse(self.seed_url)
            if parsed.netloc:
                domains.add(parsed.netloc.lower())
        return domains
