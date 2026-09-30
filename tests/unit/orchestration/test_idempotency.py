"""Unit tests for orchestration node idempotency."""

from uuid import uuid4

import pytest

from apps.worker.orchestration.events import WorkflowEventBus
from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters


@pytest.mark.asyncio
async def test_validate_inputs_idempotency():
    bus = WorkflowEventBus()
    adapters = InvestigationNodeAdapters(event_bus=bus)

    state: InvestigationWorkflowState = {
        "workflow_id": "wf-idem-1",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.PENDING.value,
        "current_phase": "validate_inputs",
        "version_a": {"base_url": "http://localhost:3000", "version_id": str(uuid4())},
        "version_b": {"base_url": "http://localhost:3001", "version_id": str(uuid4())},
        "history": [],
    }

    # Running validate once
    out1 = await adapters.validate_inputs(state)
    assert out1["current_phase"] == "validate_inputs"
    assert len(out1["history"]) == 1
    assert out1["history"][0]["status"] == "COMPLETED"

    # Running validate again with completed history
    state.update(out1)
    out2 = await adapters.validate_inputs(state)
    assert out2["current_phase"] == "validate_inputs"
    assert out2["history"][-1]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_align_idempotency():
    bus = WorkflowEventBus()
    adapters = InvestigationNodeAdapters(event_bus=bus)

    mock_alignment = {"aligned_pairs": [], "unmatched_a": [], "unmatched_b": []}
    state: InvestigationWorkflowState = {
        "workflow_id": "wf-idem-2",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.RUNNING.value,
        "alignment_result": mock_alignment,
        "history": [],
    }

    out = await adapters.align(state)
    assert out["current_phase"] == "align"
    assert out["history"][-1]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_diff_idempotency():
    bus = WorkflowEventBus()
    adapters = InvestigationNodeAdapters(event_bus=bus)

    mock_diff = {"differences": []}
    state: InvestigationWorkflowState = {
        "workflow_id": "wf-idem-3",
        "analysis_id": str(uuid4()),
        "status": WorkflowStatus.RUNNING.value,
        "semantic_diff_result": mock_diff,
        "history": [],
    }

    out = await adapters.diff(state)
    assert out["current_phase"] == "diff"
    assert out["history"][-1]["status"] == "SKIPPED"
