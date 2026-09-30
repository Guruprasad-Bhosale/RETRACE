"""Reproduction Configuration and Operational Policies."""

from pydantic import BaseModel, ConfigDict, Field


class ReplayPolicy(BaseModel):
    """Replay execution timing and strategy constraints."""

    model_config = ConfigDict(extra="forbid")

    action_timeout_ms: float = 10000.0
    stabilization_timeout_ms: float = 10000.0
    navigation_timeout_ms: float = 30000.0
    max_replay_steps: int = 50
    target_resolution_order: list[str] = Field(
        default_factory=lambda: ["testid", "role", "label", "text", "css"]
    )


class PerformanceSamplingPolicy(BaseModel):
    """Configuration for repeated measurement sampling during performance regression reproduction."""

    model_config = ConfigDict(extra="forbid")

    sample_runs: int = 3
    warmup_run: bool = False
    aggregation_statistic: str = "median"  # "median" or "mean"


class RecoveryPolicy(BaseModel):
    """Bounded precondition restoration constraints.

    Hard Invariant: Recovery may ONLY restore the expected precondition state.
    It must NEVER branch into an alternative route or change the causal experiment.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    max_recovery_attempts: int = 1
    backtrack_delay_ms: float = 500.0
    allow_path_branching: bool = False  # Strict invariant: no alternate branching


class SafetyPolicy(BaseModel):
    """Safety guard rails preventing destructive interactions or unintended network escapes."""

    model_config = ConfigDict(extra="forbid")

    block_destructive_actions: bool = True
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_keywords: list[str] = Field(
        default_factory=lambda: [
            "place order",
            "submit payment",
            "delete account",
            "cancel subscription",
            "wipe data",
            "terminate account",
            "format",
            "destroy",
        ]
    )
    allow_cross_domain_navigation: bool = False


class VerificationPolicy(BaseModel):
    """Thresholds and strictness for matching expected regression classifications."""

    model_config = ConfigDict(extra="forbid")

    require_exact_http_match: bool = True
    require_exact_route_match: bool = True
    allow_partial_match_as_reproduced: bool = False
    performance_delta_threshold_ms: float = 200.0


class ReproductionConfig(BaseModel):
    """Master configuration for the Autonomous Regression Reproduction Engine."""

    model_config = ConfigDict(extra="forbid")

    replay: ReplayPolicy = Field(default_factory=ReplayPolicy)
    performance_sampling: PerformanceSamplingPolicy = Field(default_factory=PerformanceSamplingPolicy)
    recovery: RecoveryPolicy = Field(default_factory=RecoveryPolicy)
    safety: SafetyPolicy = Field(default_factory=SafetyPolicy)
    verification: VerificationPolicy = Field(default_factory=VerificationPolicy)
    max_total_duration_sec: float = 180.0
    max_attempts_per_classification: int = 2
