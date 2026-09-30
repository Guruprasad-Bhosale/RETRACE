"""Unit tests for failure classification and diagnostic preservation."""

from uuid import uuid4

from apps.worker.orchestration.models import (
    FailureType,
    InvestigationWorkflowState,
    NodeExecutionRecord,
    WorkflowStatus,
    utc_now,
)


def test_failure_classification_mapping():
    record = NodeExecutionRecord(
        node="validate_inputs",
        status="FAILED",
        attempt=1,
        started_at=utc_now(),
        completed_at=utc_now(),
        duration_ms=10.0,
        error="Invalid application URL provided.",
    )

    state: InvestigationWorkflowState = {
        "workflow_id": "wf-123",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.FAILED.value,
        "failure_type": FailureType.INVALID_INPUT.value,
        "error_message": "Invalid application URL provided.",
        "history": [record.model_dump(mode="json")],
    }

    assert state["status"] == "FAILED"
    assert state["failure_type"] == "INVALID_INPUT"
    assert len(state["history"]) == 1
    assert state["history"][0]["status"] == "FAILED"


def test_inconclusive_classification_mapping():
    state: InvestigationWorkflowState = {
        "workflow_id": "wf-456",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.INCONCLUSIVE.value,
        "failure_type": FailureType.UPSTREAM_INCONCLUSIVE.value,
        "error_message": None,
        "history": [],
    }

    assert state["status"] == "INCONCLUSIVE"
    assert state["failure_type"] == "UPSTREAM_INCONCLUSIVE"
