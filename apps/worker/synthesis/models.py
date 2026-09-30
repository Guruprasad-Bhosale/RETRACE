"""Test Synthesis Domain Models.

Provides strongly typed models for Playwright test representation, evidence-grounded
assertions, deterministic selector resolution, and generated test provenance.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ActionType, ArtifactReference


class SynthesisStatus(StrEnum):
    """Lifecycle status of test synthesis."""

    SYNTHESIZED = "SYNTHESIZED"
    PARTIALLY_SYNTHESIZED = "PARTIALLY_SYNTHESIZED"
    INCOMPLETE = "INCOMPLETE"
    UNSUPPORTED = "UNSUPPORTED"


class ValidationStatus(StrEnum):
    """Validation status for synthesized test artifacts."""

    VALIDATED = "VALIDATED"  # Runtime validated against target
    STRUCTURALLY_VALIDATED = "STRUCTURALLY_VALIDATED"  # Passed AST/syntax/evidence checks
    VALIDATION_FAILED = "VALIDATION_FAILED"
    NOT_VALIDATED = "NOT_VALIDATED"


class TestFramework(StrEnum):
    """Target test automation frameworks."""

    __test__ = False
    PLAYWRIGHT = "PLAYWRIGHT"


class TestLanguage(StrEnum):
    """Supported test implementation languages."""

    __test__ = False
    TYPESCRIPT = "TYPESCRIPT"
    PYTHON = "PYTHON"


class AssertionCategory(StrEnum):
    """Semantic category of synthesized assertion."""

    NAVIGATION = "NAVIGATION"
    API_NETWORK = "API_NETWORK"
    UI_STATE = "UI_STATE"
    CALCULATION = "CALCULATION"
    ACCESSIBILITY = "ACCESSIBILITY"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    PERFORMANCE = "PERFORMANCE"


class SelectorStrategy(StrEnum):
    """Deterministic locator strategy utilized for a test step."""

    ROLE_AND_NAME = "ROLE_AND_NAME"
    LABEL = "LABEL"
    TEST_ID = "TEST_ID"
    STABLE_ID = "STABLE_ID"
    SEMANTIC_ATTRIBUTE = "SEMANTIC_ATTRIBUTE"
    ACTION_LOCATOR = "ACTION_LOCATOR"
    FALLBACK_CSS = "FALLBACK_CSS"


class TestStep(BaseModel):
    """Single executable action step within a synthesized test."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    step_index: int = Field(ge=0, description="0-indexed step sequence")
    action_type: ActionType
    raw_target: str | None = None
    resolved_selector: str = Field(description="Playwright-compatible locator expression")
    selector_strategy: SelectorStrategy = SelectorStrategy.ACTION_LOCATOR
    value: str | None = None
    timeout_ms: float = 10000.0
    description: str = Field(default="", description="Human-readable step description")
    source_step_index: int | None = None
    causal_context: dict[str, Any] = Field(default_factory=dict)


class TestAssertion(BaseModel):
    """An evidence-grounded assertion verifying expected vs regressed behavior."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    assertion_id: str
    category: AssertionCategory
    assertion_type: str = Field(description="Playwright assertion method, e.g. toHaveURL, toBeVisible")
    subject: str = Field(description="Locator or entity under test, e.g. page, response, locator")
    expected_value: Any = Field(description="Ground truth expected value from Phase 8 baseline evidence")
    actual_value_observed: Any = Field(
        default=None, description="Observed regressed value from Phase 8 reproduction evidence"
    )
    operator: str = "equals"
    tolerance: float | None = None
    manual_review_required: bool = False
    evidence_id: str = Field(description="Upstream evidence / difference / classification ID")
    reasoning: str = Field(description="Causal derivation linking this assertion to empirical evidence")


class TestProvenance(BaseModel):
    """Immutable provenance record establishing full origin lineage for a synthesized test."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    root_cause_id: str | None = None
    trajectory_id: UUID | None = None
    observation_ids: list[UUID] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    source_locations: list[str] = Field(default_factory=list)
    commit_hashes: list[str] = Field(default_factory=list)
    synthesized_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_deterministic_test_id(
    classification_id: str,
    reproduction_id: str | None,
    framework: TestFramework,
    language: TestLanguage,
    step_signatures: list[str],
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural test parameters."""
    raw = f"{classification_id}:{reproduction_id or ''}:{framework.value}:{language.value}:{';'.join(step_signatures)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class GeneratedTest(BaseModel):
    """Complete, self-contained executable regression test artifact."""

    model_config = ConfigDict(extra="forbid")

    test_id: str
    regression_id: str
    reproduction_id: str | None = None
    root_cause_id: str | None = None
    framework: TestFramework = TestFramework.PLAYWRIGHT
    language: TestLanguage = TestLanguage.TYPESCRIPT
    target_version: str = "A_B_DUAL"  # "A_B_DUAL", "VERSION_A", "VERSION_B"
    title: str = Field(description="Concise descriptive title for the test suite")
    description: str = Field(description="Contextual explanation of what regression is caught")
    steps: list[TestStep] = Field(default_factory=list)
    assertions: list[TestAssertion] = Field(default_factory=list)
    provenance: TestProvenance
    status: SynthesisStatus = SynthesisStatus.SYNTHESIZED
    validation_status: ValidationStatus = ValidationStatus.NOT_VALIDATED
    generated_source: str = Field(description="Executable TypeScript/Python test source code")
    validation_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    # created_at is observational metadata ONLY and must never participate in test_id or sorting
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.status.value,
            self.framework.value,
            self.test_id,
        )


class SynthesisSummary(BaseModel):
    """Statistical summary count of synthesized tests."""

    model_config = ConfigDict(extra="forbid")

    total_regressions_analyzed: int = 0
    synthesized_count: int = 0
    partially_synthesized_count: int = 0
    incomplete_count: int = 0
    unsupported_count: int = 0
    structurally_validated_count: int = 0
    runtime_validated_count: int = 0


class SynthesisSuiteResult(BaseModel):
    """Top-level immutable container holding all synthesized test artifacts in a run."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    tests: list[GeneratedTest] = Field(default_factory=list)
    summary: SynthesisSummary = Field(default_factory=SynthesisSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
