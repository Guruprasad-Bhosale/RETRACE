"""RETRACE Workflow Orchestration Domain Models & State Definitions.

Canonical state representations, typed events, failure classifications,
and execution budgets for the LangGraph orchestration runtime.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypedDict
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


class WorkflowStatus(StrEnum):
    """Execution status of an orchestrated investigation workflow."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FailureType(StrEnum):
    """Categorized failure types for deterministic recovery and bounded retries."""

    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    INVALID_INPUT = "INVALID_INPUT"
    SECURITY_FAILURE = "SECURITY_FAILURE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    UPSTREAM_INCONCLUSIVE = "UPSTREAM_INCONCLUSIVE"


class WorkflowEventType(StrEnum):
    """Structured lifecycle events emitted during workflow execution."""

    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    NODE_STARTED = "NODE_STARTED"
    NODE_COMPLETED = "NODE_COMPLETED"
    NODE_RETRIED = "NODE_RETRIED"
    NODE_FAILED = "NODE_FAILED"
    NODE_SKIPPED = "NODE_SKIPPED"
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"
    WORKFLOW_RESUMED = "WORKFLOW_RESUMED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    WORKFLOW_INCONCLUSIVE = "WORKFLOW_INCONCLUSIVE"
    WORKFLOW_CANCELLED = "WORKFLOW_CANCELLED"


class WorkflowEvent(BaseModel):
    """Operational event record emitted at state transitions."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: WorkflowEventType
    workflow_id: str
    analysis_id: UUID
    node_name: str | None = None
    attempt: int = 1
    timestamp: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class NodeExecutionRecord(BaseModel):
    """Audit record for a single graph node execution."""

    model_config = ConfigDict(extra="allow")

    node_name: str | None = None
    node: str | None = None
    status: str  # COMPLETED, FAILED, SKIPPED, CANCELLED
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    attempt: int = 1
    error: str | None = None

    def __init__(self, **data: Any) -> None:
        if "node" in data and "node_name" not in data:
            data["node_name"] = data["node"]
        elif "node_name" in data and "node" not in data:
            data["node"] = data["node_name"]
        super().__init__(**data)


class VersionConfig(BaseModel):
    """Configuration for a target application version."""

    model_config = ConfigDict(extra="allow")

    base_url: str
    repository_path: str | None = None
    version_id: UUID = Field(default_factory=uuid4)
    name: str = "v1"


class ResourceBudget(BaseModel):
    """Explicit resource constraints governing workflow execution."""

    model_config = ConfigDict(extra="allow")

    max_workflow_duration_s: int = 600
    max_node_duration_s: int = 120
    max_workflow_duration_sec: int = 600
    max_node_duration_sec: int = 120
    max_exploration_steps: int = 15
    max_reproduction_attempts: int = 3
    max_retries_per_node: int = 2
    max_concurrent_browsers: int = 2

    def __init__(self, **data: Any) -> None:
        if "max_workflow_duration_sec" in data and "max_workflow_duration_s" not in data:
            data["max_workflow_duration_s"] = data["max_workflow_duration_sec"]
        elif "max_workflow_duration_s" in data and "max_workflow_duration_sec" not in data:
            data["max_workflow_duration_sec"] = data["max_workflow_duration_s"]

        if "max_node_duration_sec" in data and "max_node_duration_s" not in data:
            data["max_node_duration_s"] = data["max_node_duration_sec"]
        elif "max_node_duration_s" in data and "max_node_duration_sec" not in data:
            data["max_node_duration_sec"] = data["max_node_duration_s"]

        super().__init__(**data)


class ExecutionPolicy(BaseModel):
    """Execution policy controlling concurrency and runtime features."""

    model_config = ConfigDict(extra="allow")

    allow_parallel_exploration: bool = True
    llm_enabled: bool = False
    retry_transient_failures: bool = True
    max_retries: int = 2
    retry_on_transient: bool = True
    fail_fast: bool = False


class InvestigationRequest(BaseModel):
    """Input payload initiating an end-to-end autonomous investigation."""

    model_config = ConfigDict(extra="allow")

    project_id: str = "default"
    version_a: VersionConfig
    version_b: VersionConfig
    analysis_id: UUID = Field(default_factory=uuid4)
    budget: ResourceBudget = Field(default_factory=ResourceBudget)
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("project_id", mode="before")
    @classmethod
    def convert_project_id(cls, v: Any) -> str:
        return str(v)


class InvestigationWorkflowState(TypedDict, total=False):
    """Canonical mutable state object passed across LangGraph nodes."""

    workflow_id: str
    project_id: str
    analysis_id: str
    version_a: dict[str, Any]
    version_b: dict[str, Any]
    budget: dict[str, Any]
    policy: dict[str, Any]
    status: str
    current_phase: str
    cancellation_requested: bool

    # Subsystem outputs (in-memory or serialized)
    exploration_result_a: Any
    exploration_result_b: Any
    alignment_result: Any
    semantic_diff_result: Any
    classification_result: Any
    reproduction_suite: Any
    root_cause_suite: Any
    investigation_suite: Any

    # Provenance & Audit
    artifacts: list[dict[str, Any]]
    history: list[dict[str, Any]]
    events: list[dict[str, Any]]
    diagnostics: dict[str, Any]

    # Error & Recovery
    error_message: str | None
    failure_type: str | None
    retry_counts: dict[str, int]
