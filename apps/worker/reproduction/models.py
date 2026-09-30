"""Reproduction Domain Models and Strongly Typed Value Objects.

Provides authoritative domain entities for deterministic causal path representation,
dual-version replay observations, expected vs actual verification, and structured reproduction persistence.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ActionType, ArtifactReference


class ReproductionStatus(StrEnum):
    """Lifecycle status of a regression reproduction."""

    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    REPRODUCED = "REPRODUCED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ReproductionStrategy(StrEnum):
    """Replay execution strategy."""

    DIRECT_REPLAY = "DIRECT_REPLAY"
    VERIFIED_REPLAY = "VERIFIED_REPLAY"
    RECOVERY_REPLAY = "RECOVERY_REPLAY"


class MatchStatus(StrEnum):
    """Granular comparison match outcome between expected regression and fresh evidence."""

    FULL_MATCH = "FULL_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_MATCH = "NO_MATCH"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class OriginalEvidence(BaseModel):
    """Historical evidence lineage from Phase 4-7 preceding reproduction."""

    model_config = ConfigDict(extra="forbid")

    observation_id: UUID | None = None
    state_id: str | None = None
    action_id: str | None = None
    transition_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ReproductionObservation(BaseModel):
    """Fresh state observation captured during deterministic reproduction replay."""

    model_config = ConfigDict(extra="forbid")

    reproduction_observation_id: UUID = Field(default_factory=uuid4)
    version_id: UUID
    step_index: int = Field(ge=0)
    url: str
    http_status: int | None = None
    dom_hash: str | None = None
    a11y_tree_hash: str | None = None
    page_title: str | None = None
    console_errors_count: int = 0
    console_warnings_count: int = 0
    page_errors_count: int = 0
    network_failures_count: int = 0
    interactive_elements_count: int = 0
    duration_ms: float = 0.0
    action_success: bool = True
    error_message: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReproductionEvidence(BaseModel):
    """Fresh multi-modal reproduction evidence captured across Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    attempt_id: UUID = Field(default_factory=uuid4)
    observations_a: list[ReproductionObservation] = Field(default_factory=list)
    observations_b: list[ReproductionObservation] = Field(default_factory=list)
    sample_measurements_ms_a: list[float] = Field(default_factory=list)
    sample_measurements_ms_b: list[float] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ReproductionStep(BaseModel):
    """Single ordered causal step in a deterministic reproduction path."""

    model_config = ConfigDict(extra="forbid")

    step_index: int = Field(ge=0)
    action_type: ActionType
    stable_target_identity: str | None = None
    target_role: str | None = None
    accessible_name: str | None = None
    target_strategy: str = "auto"
    raw_target: str | None = None
    value: str | None = None
    coordinates: tuple[float, float] | None = None
    expected_from_state_id: str | None = None
    expected_to_state_id: str | None = None
    source_action_id: str | None = None
    source_transition_id: str | None = None
    timeout_ms: float = 10000.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_step_signature(self) -> str:
        """Deterministic step signature for path identity."""
        return (
            f"step={self.step_index}|type={self.action_type.value}|"
            f"target={self.stable_target_identity or ''}|role={self.target_role or ''}|"
            f"name={self.accessible_name or ''}|val={self.value or ''}"
        )


class ReproductionPath(BaseModel):
    """Deterministic, minimal causal path extracted for regression reproduction."""

    model_config = ConfigDict(extra="forbid")

    path_id: str
    trajectory_id: UUID
    classification_id: str
    difference_id: str
    seed_url: str
    steps: list[ReproductionStep] = Field(default_factory=list)
    path_signature: str
    state_ids: list[str] = Field(default_factory=list)
    transition_ids: list[str] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)
    observation_ids: list[UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReproductionVerification(BaseModel):
    """Verifiable comparison between expected regression classification and fresh evidence."""

    model_config = ConfigDict(extra="forbid")

    expected_difference_id: str
    expected_classification_id: str
    expected_rule_id: str
    expected_category: str
    match_status: MatchStatus
    observed_match: bool
    matched_evidence: list[str] = Field(default_factory=list)
    mismatched_evidence: list[str] = Field(default_factory=list)
    notes: str = ""
    observed_difference_summary: dict[str, Any] = Field(default_factory=dict)


class ReproductionAttemptResult(BaseModel):
    """Outcome of a single execution attempt within a reproduction task."""

    model_config = ConfigDict(extra="forbid")

    attempt_id: UUID = Field(default_factory=uuid4)
    attempt_number: int = Field(ge=1)
    strategy: ReproductionStrategy
    status: ReproductionStatus
    verification: ReproductionVerification | None = None
    evidence: ReproductionEvidence
    failure_reason: str | None = None
    duration_ms: float = 0.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


def compute_deterministic_reproduction_id(
    classification_id: str,
    version_a_id: UUID,
    version_b_id: UUID,
    trajectory_id: UUID,
    path_signature: str,
    strategy: ReproductionStrategy,
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural reproduction parameters."""
    raw = (
        f"{classification_id}:{version_a_id}:{version_b_id}:"
        f"{trajectory_id}:{path_signature}:{strategy.value}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class ReproductionResult(BaseModel):
    """Complete authoritative outcome of reproducing a single classified regression."""

    model_config = ConfigDict(extra="forbid")

    reproduction_id: str
    classification_id: str
    difference_id: str
    rule_id: str
    category: str
    status: ReproductionStatus
    strategy: ReproductionStrategy
    path: ReproductionPath
    attempts: list[ReproductionAttemptResult] = Field(default_factory=list)
    final_verification: ReproductionVerification | None = None
    total_duration_ms: float = 0.0
    # created_at is observational metadata ONLY and must never participate in deterministic identity or sorting
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def deterministic_sort_key(self) -> tuple[str, str, str, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.category,
            self.status.value,
            self.rule_id,
            self.reproduction_id,
        )


class ReproductionSummary(BaseModel):
    """Statistical summary of reproduction executions."""

    model_config = ConfigDict(extra="forbid")

    total_reproductions_attempted: int = 0
    reproduced: int = 0
    not_reproduced: int = 0
    inconclusive: int = 0
    blocked: int = 0
    failed: int = 0


class ReproductionSuiteResult(BaseModel):
    """Top-level immutable container for all reproduction results in an analysis run."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    trajectory_a_id: UUID
    trajectory_b_id: UUID
    results: list[ReproductionResult] = Field(default_factory=list)
    summary: ReproductionSummary = Field(default_factory=ReproductionSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
