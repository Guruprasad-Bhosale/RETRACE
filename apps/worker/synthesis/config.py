"""Test Synthesis Configuration and Policies.

Provides operational configurations for Playwright TypeScript test generation,
selector prioritization rules, and evidence-grounded assertion bounds.
"""

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.synthesis.models import SelectorStrategy, TestFramework, TestLanguage


class SynthesisConfig(BaseModel):
    """Configuration for Playwright test synthesis."""

    model_config = ConfigDict(extra="forbid")

    framework: TestFramework = TestFramework.PLAYWRIGHT
    language: TestLanguage = TestLanguage.TYPESCRIPT
    default_timeout_ms: float = Field(default=10000.0, ge=1000.0, le=60000.0)
    action_delay_ms: float = Field(default=200.0, ge=0.0, le=5000.0)
    include_ab_dual_mode: bool = Field(
        default=True, description="Generate test with parameterizable BASELINE and TARGET URLs"
    )
    baseline_env_var: str = "RETRACE_BASE_URL"
    target_env_var: str = "RETRACE_TARGET_URL"
    selector_preferences: list[SelectorStrategy] = Field(
        default_factory=lambda: [
            SelectorStrategy.ROLE_AND_NAME,
            SelectorStrategy.LABEL,
            SelectorStrategy.TEST_ID,
            SelectorStrategy.STABLE_ID,
            SelectorStrategy.SEMANTIC_ATTRIBUTE,
            SelectorStrategy.ACTION_LOCATOR,
            SelectorStrategy.FALLBACK_CSS,
        ]
    )
    min_performance_samples_for_assertion: int = Field(
        default=3, description="Minimum repeated measurements in Phase 8 required for bounded timing assertion"
    )
    calculation_relative_tolerance: float = 0.0001
    sanitize_volatile_api_fields: bool = True
