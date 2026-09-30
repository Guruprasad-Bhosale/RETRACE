"""Semantic Difference Engine Configuration.

Defines deterministic feature toggles, normalization policies, and comparison options.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiffConfig(BaseModel):
    """Configuration options for the Semantic Difference Engine."""

    model_config = ConfigDict(extra="forbid")

    enable_state_diff: bool = True
    enable_route_diff: bool = True
    enable_action_diff: bool = True
    enable_transition_diff: bool = True
    enable_dom_diff: bool = True
    enable_a11y_diff: bool = True
    enable_interaction_diff: bool = True
    enable_network_diff: bool = True
    enable_console_diff: bool = True
    enable_performance_diff: bool = True

    route_matching_policy: Literal["strict", "strip_query", "allow_aliases"] = "strip_query"
    route_aliases: dict[str, list[str]] = Field(default_factory=dict)

    # Observational thresholds strictly for noise filtering (not severity/judgment)
    timing_min_observable_delta_ms: float = Field(
        default=50.0,
        description="Minimum duration delta in ms to record as an observational difference.",
    )
