"""Regression Classification Engine Configuration and Policies.

Defines explicit thresholds, feature toggles, and deterministic evaluation policies.
"""

from pydantic import BaseModel, ConfigDict, Field


class PerformancePolicy(BaseModel):
    """Configurable absolute timing thresholds for performance regression candidate identification."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    navigation_delta_threshold_ms: float = Field(
        default=1000.0,
        description="Absolute duration increase in ms (B - A >= threshold) to classify as performance regression candidate.",
    )
    network_delta_threshold_ms: float = Field(
        default=1000.0,
        description="Absolute network latency increase in ms (B - A >= threshold) to classify as regression candidate.",
    )
    stabilization_delta_threshold_ms: float = Field(
        default=1000.0,
        description="Absolute page stabilization duration increase in ms (B - A >= threshold) to classify as regression candidate.",
    )


class RuntimeErrorPolicy(BaseModel):
    """Policy for console error and runtime script exception classification."""

    model_config = ConfigDict(extra="forbid")

    treat_console_errors_as_candidates: bool = True
    treat_warnings_as_candidates: bool = False


class AccessibilityPolicy(BaseModel):
    """Policy for accessibility structural and state classification."""

    model_config = ConfigDict(extra="forbid")

    classify_hash_only_as_unclassified: bool = True


class ClassificationPolicy(BaseModel):
    """Global classification behavior policies."""

    model_config = ConfigDict(extra="forbid")

    allow_multiple_classifications_per_diff: bool = True


class RegressionConfig(BaseModel):
    """Root configuration for the Regression Classification Engine."""

    model_config = ConfigDict(extra="forbid")

    performance: PerformancePolicy = Field(default_factory=PerformancePolicy)
    runtime: RuntimeErrorPolicy = Field(default_factory=RuntimeErrorPolicy)
    accessibility: AccessibilityPolicy = Field(default_factory=AccessibilityPolicy)
    classification: ClassificationPolicy = Field(default_factory=ClassificationPolicy)
