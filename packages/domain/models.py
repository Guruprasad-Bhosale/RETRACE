"""RETRACE Core Domain Models, Value Objects, and Trajectory Entities.

Implements pure domain entities with strong typing, sequence semantics,
immutable provenance, multi-attempt reproductions, and distinct root cause hypotheses.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


# ------------------------------------------------------------------------------
# Controlled Lifecycle & Category Enums
# ------------------------------------------------------------------------------


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    ANALYZING = "analyzing"
    REPRODUCING = "reproducing"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingCategory(StrEnum):
    FUNCTIONAL = "functional"
    API_CONTRACT = "api_contract"
    VISUAL = "visual"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    STATE_PERSISTENCE = "state_persistence"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VerificationStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    UNVERIFIED = "unverified"


class EvidenceType(StrEnum):
    DOM_DIFF = "dom_diff"
    ACCESSIBILITY_DIFF = "accessibility_diff"
    NETWORK_REQUEST = "network_request"
    NETWORK_RESPONSE = "network_response"
    CONSOLE_ERROR = "console_error"
    SCREENSHOT = "screenshot"
    VISUAL_DIFF = "visual_diff"
    PERFORMANCE_TIMING = "performance_timing"
    GIT_DIFF = "git_diff"
    SOURCE_CODE_AST = "source_code_ast"
    PLAYWRIGHT_TRACE = "playwright_trace"


class ArtifactKind(StrEnum):
    SCREENSHOT = "screenshot"
    DOM_SNAPSHOT = "dom_snapshot"
    A11Y_TREE = "a11y_tree"
    HAR_TRACE = "har_trace"
    PLAYWRIGHT_TRACE = "playwright_trace"
    VIDEO = "video"
    CONSOLE_LOG = "console_log"
    SOURCE_FILE = "source_file"
    GENERATED_TEST = "generated_test"
    DIFF_PATCH = "diff_patch"


class ActionType(StrEnum):
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    WAIT = "wait"
    PRESS_KEY = "press_key"
    CUSTOM = "custom"


class ReproductionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class HypothesisType(StrEnum):
    OBSERVED_FACT = "observed_fact"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"


# ------------------------------------------------------------------------------
# Base Domain Model & Shared Value Objects
# ------------------------------------------------------------------------------


class BaseDomainModel(BaseModel):
    """Base domain model with strict type validation."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",
    )


class ArtifactReference(BaseDomainModel):
    """First-class typed reference to a persisted multi-modal artifact."""

    id: UUID = Field(default_factory=uuid4)
    kind: ArtifactKind
    storage_uri: str = Field(description="Storage URI from ArtifactStorage, e.g. file:// or s3://")
    mime_type: str = Field(default="application/octet-stream")
    size_bytes: int = Field(default=0, ge=0)
    sha256_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Provenance(BaseDomainModel):
    """Immutable provenance record establishing full origin context for observations & evidence."""

    analysis_id: UUID
    version_id: UUID
    trajectory_id: UUID | None = None
    step_index: int = Field(default=0, ge=0)
    collected_at: datetime = Field(default_factory=utc_now)
    collector_service: str = Field(default="browser-observation-engine")
    environment_context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationStateSnapshot(BaseDomainModel):
    """Deep structural and behavioral state of the application at a single point in time."""

    url: str
    page_title: str | None = None
    http_status: int | None = None
    viewport: dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})
    dom_hash: str | None = None
    a11y_tree_hash: str | None = None
    console_errors_count: int = Field(default=0, ge=0)
    console_warnings_count: int = Field(default=0, ge=0)
    network_requests_count: int = Field(default=0, ge=0)
    network_failures_count: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    interactive_elements_count: int = Field(default=0, ge=0)
    summary: dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------------------
# Core Entities
# ------------------------------------------------------------------------------


class ApplicationVersion(BaseDomainModel):
    """Represents a specific application deployment/version under test."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    name: str = Field(
        min_length=1, max_length=128, description="Display label, e.g. Baseline (v1.0.0)"
    )
    base_url: str = Field(description="Base URL where this version is hosted and accessible")
    git_repo_url: str | None = Field(default=None, description="Git repository URL if available")
    git_commit_hash: str | None = Field(
        default=None, description="Commit hash corresponding to this build"
    )
    branch: str | None = None
    build_id: str | None = None
    environment_variables: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Project(BaseDomainModel):
    """A project containing test configurations and historical analysis sessions."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Trajectory(BaseDomainModel):
    """An ordered exploration sequence executed against a specific application version."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    version_id: UUID
    name: str = Field(default="Main Exploration Trajectory", max_length=128)
    status: str = Field(default="active")
    step_count: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Action(BaseDomainModel):
    """An interaction executed on a page by the explorer, maintaining trajectory sequence order."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    version_id: UUID
    trajectory_id: UUID
    step_index: int = Field(ge=0, description="0-indexed position in action trajectory")
    action_type: ActionType
    selector: str | None = None
    value: str | None = None
    coordinates: tuple[float, float] | None = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    prior_observation_id: UUID | None = Field(
        default=None, description="Observation state immediately before action execution"
    )
    resulting_observation_id: UUID | None = Field(
        default=None, description="Observation state reached following action execution"
    )
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(BaseDomainModel):
    """Deterministic, rich state snapshot at a specific step in an action trajectory."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    version_id: UUID
    trajectory_id: UUID
    step_index: int = Field(ge=0, description="0-indexed position in action trajectory")
    state: ApplicationStateSnapshot
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    provenance: Provenance
    prior_observation_id: UUID | None = None
    caused_by_action_id: UUID | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class Evidence(BaseDomainModel):
    """Verifiable piece of evidence supporting or refuting a finding, with immutable provenance."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    version_id: UUID | None = None
    trajectory_id: UUID | None = None
    observation_id: UUID | None = None
    finding_id: UUID | None = None
    evidence_type: EvidenceType
    description: str = Field(description="Human and machine readable description of evidence")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Structured deterministic payload (e.g. diff JSON)"
    )
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    provenance: Provenance
    collected_at: datetime = Field(default_factory=utc_now)


class ReproductionAttempt(BaseDomainModel):
    """An execution attempt to reproduce a candidate regression (supports multiple attempts)."""

    id: UUID = Field(default_factory=uuid4)
    finding_id: UUID
    session_id: UUID
    attempt_number: int = Field(ge=1, description="1-indexed reproduction attempt sequence")
    framework: Literal["playwright_python", "playwright_typescript"] = "playwright_python"
    script_code: str = Field(description="Self-contained executable Playwright reproduction test")
    status: ReproductionStatus = ReproductionStatus.SKIPPED
    execution_output: str | None = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class RootCause(BaseDomainModel):
    """Correlated root cause hypothesis, cleanly distinguishing observed facts from hypotheses."""

    id: UUID = Field(default_factory=uuid4)
    finding_id: UUID
    session_id: UUID
    hypothesis_type: HypothesisType = HypothesisType.HYPOTHESIS
    commit_hash: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    diff_chunk: str | None = None
    explanation: str = Field(description="Detailed engineering reasoning for the defect")
    confidence: float = Field(ge=0.0, le=1.0, description="Bayesian / heuristic confidence score")
    affected_components: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class Finding(BaseDomainModel):
    """A detected behavioral or contract regression between Version A and Version B."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    category: FindingCategory
    severity: FindingSeverity
    title: str = Field(min_length=1, max_length=256)
    description: str
    workflow_path: list[str] = Field(default_factory=list, description="Sequence of actions/routes")
    confidence: float = Field(ge=0.0, le=1.0)
    status: VerificationStatus = VerificationStatus.CANDIDATE
    evidence_ids: list[UUID] = Field(default_factory=list)
    reproductions: list[ReproductionAttempt] = Field(default_factory=list)
    root_causes: list[RootCause] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class AnalysisSession(BaseDomainModel):
    """Complete analysis execution comparing Version A against Version B with optimistic locking."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    version_a: ApplicationVersion
    version_b: ApplicationVersion
    status: AnalysisStatus = AnalysisStatus.PENDING
    version: int = Field(default=1, ge=1, description="Optimistic concurrency locking version")
    config: dict[str, Any] = Field(default_factory=dict)
    workflows_explored: int = Field(default=0, ge=0)
    regressions_count: int = Field(default=0, ge=0)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Report(BaseDomainModel):
    """Derived engineering investigation report synthesized from authoritative domain entities."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    total_workflows: int = Field(default=0, ge=0)
    verified_regressions: int = Field(default=0, ge=0)
    false_positives_filtered: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
