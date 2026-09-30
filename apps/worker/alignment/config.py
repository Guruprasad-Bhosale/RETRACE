"""Alignment Configuration Module.

Strongly-typed deterministic configuration for Version A/B behavioral trajectory alignment.
Zero LLM, zero probabilistic models, zero arbitrary numeric thresholds.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AlignmentConfig(BaseModel):
    """Configuration governing deterministic trajectory graph alignment between Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    version_a_base_url: str = Field(
        default="http://localhost:3001",
        description="Base URL for baseline Version A application.",
    )
    version_b_base_url: str = Field(
        default="http://localhost:3002",
        description="Base URL for target Version B application.",
    )
    route_matching_policy: Literal["exact", "strip_query", "allow_aliases"] = Field(
        default="exact",
        description="Policy for comparing application route paths.",
    )
    route_aliases: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Configurable map of equivalent route aliases (e.g. {'/': ['/home', '/index.html']}).",
    )
    deterministic_tie_breaker: str = Field(
        default="lexicographical",
        description="Tie-breaking method when resolving equal-evidence candidate pairings.",
    )
