"""Integration test for cooperative workflow cancellation."""

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import MemorySaver

from apps.worker.orchestration.graph import create_investigation_graph
from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters


@pytest.mark.asyncio
async def test_workflow_cancellation_during_execution():
    checkpointer = MemorySaver()
    adapters = InvestigationNodeAdapters()
    graph = create_investigation_graph(adapters, checkpointer=checkpointer)

    initial_state: InvestigationWorkflowState = {
        "workflow_id": "wf-cancel-integ-1",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.RUNNING.value,
        "current_phase": "start",
        "version_a": {"base_url": "http://localhost:3000", "version_id": str(uuid4())},
        "version_b": {"base_url": "http://localhost:3001", "version_id": str(uuid4())},
        "history": [],
        "artifacts": [],
        "cancellation_requested": True,  # User requested cancellation
    }

    config = {"configurable": {"thread_id": "wf-cancel-integ-1"}}
    final_state = await graph.ainvoke(initial_state, config=config)

    assert final_state["status"] == WorkflowStatus.CANCELLED.value
    assert len(final_state["history"]) > 0
    assert final_state["history"][-1]["status"] == "CANCELLED"
