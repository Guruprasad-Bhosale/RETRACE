"""Resilience tests for Workflow Cancellation, Timeout Enforcement, and Resource Budgets."""

from uuid import uuid4

import pytest

from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters


@pytest.mark.asyncio
async def test_workflow_cancellation_at_input_validation():
    """Verify workflow cancels immediately when cancellation_requested flag is set at entry."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": str(uuid4()),
        "analysis_id": str(uuid4()),
        "project_id": str(uuid4()),
        "version_a": {"base_url": "http://localhost:3000"},
        "version_b": {"base_url": "http://localhost:3001"},
        "status": WorkflowStatus.RUNNING.value,
        "cancellation_requested": True,
        "history": [],
        "retry_counts": {},
    }

    result_state = await adapters.validate_inputs(state)
    assert result_state["status"] == WorkflowStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_workflow_cancellation_at_explore_boundary():
    """Verify workflow cancels before exploration begins when cancelled flag is detected."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": str(uuid4()),
        "analysis_id": str(uuid4()),
        "project_id": str(uuid4()),
        "version_a": {"base_url": "http://localhost:3000"},
        "version_b": {"base_url": "http://localhost:3001"},
        "status": WorkflowStatus.RUNNING.value,
        "cancellation_requested": True,
        "history": [],
        "retry_counts": {},
    }

    result_state = await adapters.explore(state)
    assert result_state["status"] == WorkflowStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_workflow_cancellation_at_reproduction_boundary():
    """Verify workflow cancels before reproduction executes when cancelled."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": str(uuid4()),
        "analysis_id": str(uuid4()),
        "project_id": str(uuid4()),
        "version_a": {"base_url": "http://localhost:3000"},
        "version_b": {"base_url": "http://localhost:3001"},
        "status": WorkflowStatus.RUNNING.value,
        "cancellation_requested": True,
        "history": [],
        "retry_counts": {},
    }

    result_state = await adapters.reproduce(state)
    assert result_state["status"] == WorkflowStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_validate_inputs_rejects_empty_base_urls():
    """Verify validation node fails cleanly when version base URLs are empty."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": str(uuid4()),
        "analysis_id": str(uuid4()),
        "project_id": str(uuid4()),
        "version_a": {"base_url": ""},
        "version_b": {"base_url": "http://localhost:3001"},
        "status": WorkflowStatus.RUNNING.value,
        "cancellation_requested": False,
        "history": [],
        "retry_counts": {},
    }

    result_state = await adapters.validate_inputs(state)
    assert result_state["status"] == WorkflowStatus.FAILED.value
    assert "Version A base_url is required" in result_state["error_message"]
