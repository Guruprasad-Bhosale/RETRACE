"""Unit tests for workflow provenance and execution history."""

from uuid import uuid4

from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    NodeExecutionRecord,
    WorkflowStatus,
    utc_now,
)


def test_node_execution_history_provenance():
    now = utc_now()
    history = [
        NodeExecutionRecord(
            node="validate_inputs",
            status="COMPLETED",
            attempt=1,
            started_at=now,
            completed_at=now,
            duration_ms=45.2,
        ),
        NodeExecutionRecord(
            node="prepare_versions",
            status="COMPLETED",
            attempt=1,
            started_at=now,
            completed_at=now,
            duration_ms=120.5,
        ),
        NodeExecutionRecord(
            node="explore",
            status="COMPLETED",
            attempt=1,
            started_at=now,
            completed_at=now,
            duration_ms=3500.0,
        ),
    ]

    state: InvestigationWorkflowState = {
        "workflow_id": "wf-prov-1",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.RUNNING.value,
        "history": [h.model_dump(mode="json") for h in history],
        "artifacts": [{"artifact_id": "art-1", "storage_key": "obs/1"}],
    }

    assert len(state["history"]) == 3
    assert state["history"][0]["node_name"] == "validate_inputs"
    assert state["history"][1]["node_name"] == "prepare_versions"
    assert state["history"][2]["node_name"] == "explore"
    assert len(state["artifacts"]) == 1
