"""Unit tests for durable checkpointing in orchestration."""

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
async def test_memory_saver_checkpointing():
    checkpointer = MemorySaver()
    adapters = InvestigationNodeAdapters()
    graph = create_investigation_graph(adapters, checkpointer=checkpointer)

    initial_state: InvestigationWorkflowState = {
        "workflow_id": "wf-ckpt-1",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.PENDING.value,
        "current_phase": "start",
        "version_a": {"base_url": "", "version_id": str(uuid4())},
        "version_b": {"base_url": "", "version_id": str(uuid4())},
        "history": [],
        "artifacts": [],
        "cancellation_requested": False,
    }

    config = {"configurable": {"thread_id": "wf-ckpt-1"}}
    # Execute graph until failure on empty URL
    _ = await graph.ainvoke(initial_state, config=config)

    # Verify that checkpoint state exists in graph
    checkpoint_state = graph.get_state(config)
    assert checkpoint_state is not None
    assert checkpoint_state.values.get("workflow_id") == "wf-ckpt-1"
    assert checkpoint_state.values.get("status") == WorkflowStatus.FAILED.value
