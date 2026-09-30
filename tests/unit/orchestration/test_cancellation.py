"""Unit tests for cooperative workflow cancellation."""

from uuid import uuid4

import pytest

from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters
from apps.worker.orchestration.runner import InvestigationWorkflowRunner


@pytest.mark.asyncio
async def test_node_cooperative_cancellation_check():
    """Verify nodes immediately abort when cancellation is requested."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": "wf_cancel_01",
        "analysis_id": str(uuid4()),
        "cancellation_requested": True,
        "version_a": {"base_url": "http://localhost:3000"},
        "version_b": {"base_url": "http://localhost:3001"},
        "history": [],
    }

    res = await adapters.validate_inputs(state)
    assert res["status"] == WorkflowStatus.CANCELLED.value
    assert len(res["history"]) == 1
    assert res["history"][0]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_runner_cancel_method():
    """Verify runner cancel marks active state as cancelled."""
    runner = InvestigationWorkflowRunner()
    workflow_id = "wf_run_cancel_01"
    runner._active_states[workflow_id] = {
        "workflow_id": workflow_id,
        "cancellation_requested": False,
        "status": WorkflowStatus.RUNNING.value,
    }

    cancelled = await runner.cancel(workflow_id)
    assert cancelled is True
    assert runner._active_states[workflow_id]["cancellation_requested"] is True
    assert runner._active_states[workflow_id]["status"] == WorkflowStatus.CANCELLED.value
