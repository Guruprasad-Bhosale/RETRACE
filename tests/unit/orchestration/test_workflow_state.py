"""Unit tests for workflow state model, events, and request payloads."""

from uuid import uuid4

from apps.worker.orchestration.models import (
    FailureType,
    InvestigationRequest,
    NodeExecutionRecord,
    VersionConfig,
    WorkflowEvent,
    WorkflowEventType,
    WorkflowStatus,
    utc_now,
)


def test_workflow_status_and_failure_types():
    """Verify enum invariants for workflow statuses and failure classifications."""
    assert WorkflowStatus.PENDING == "PENDING"
    assert WorkflowStatus.RUNNING == "RUNNING"
    assert WorkflowStatus.COMPLETED == "COMPLETED"
    assert WorkflowStatus.INCONCLUSIVE == "INCONCLUSIVE"
    assert WorkflowStatus.FAILED == "FAILED"
    assert WorkflowStatus.CANCELLED == "CANCELLED"

    assert FailureType.TRANSIENT_FAILURE == "TRANSIENT_FAILURE"
    assert FailureType.PERMANENT_FAILURE == "PERMANENT_FAILURE"
    assert FailureType.INVALID_INPUT == "INVALID_INPUT"
    assert FailureType.SECURITY_FAILURE == "SECURITY_FAILURE"
    assert FailureType.RESOURCE_EXHAUSTION == "RESOURCE_EXHAUSTION"
    assert FailureType.UPSTREAM_INCONCLUSIVE == "UPSTREAM_INCONCLUSIVE"


def test_workflow_event_model():
    """Verify structured workflow event creation and timestamp tracking."""
    analysis_id = uuid4()
    event = WorkflowEvent(
        event_type=WorkflowEventType.NODE_COMPLETED,
        workflow_id="wf_test_01",
        analysis_id=analysis_id,
        node_name="classify",
        attempt=1,
        details={"candidates": 2},
    )

    assert event.event_type == WorkflowEventType.NODE_COMPLETED
    assert event.workflow_id == "wf_test_01"
    assert event.analysis_id == analysis_id
    assert event.node_name == "classify"
    assert event.details["candidates"] == 2
    assert event.timestamp is not None


def test_node_execution_record():
    """Verify audit record capturing execution timing and errors."""
    t1 = utc_now()
    t2 = utc_now()
    record = NodeExecutionRecord(
        node_name="reproduce",
        status="COMPLETED",
        started_at=t1,
        completed_at=t2,
        duration_ms=45.2,
        attempt=1,
    )

    assert record.node_name == "reproduce"
    assert record.status == "COMPLETED"
    assert record.duration_ms == 45.2
    assert record.error is None


def test_investigation_request_validation():
    """Verify request validation and defaults."""
    req = InvestigationRequest(
        project_id="commerce-project",
        version_a=VersionConfig(base_url="http://localhost:3000"),
        version_b=VersionConfig(base_url="http://localhost:3001"),
    )

    assert req.project_id == "commerce-project"
    assert req.version_a.base_url == "http://localhost:3000"
    assert req.version_b.base_url == "http://localhost:3001"
    assert req.budget.max_workflow_duration_s == 600
    assert req.policy.allow_parallel_exploration is True
    assert req.policy.llm_enabled is False  # LLM must be disabled by default
