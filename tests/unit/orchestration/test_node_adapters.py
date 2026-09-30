"""Unit tests for individual orchestration node adapter behaviors."""

from uuid import uuid4

import pytest

from apps.worker.orchestration.models import (
    FailureType,
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters


@pytest.mark.asyncio
async def test_validate_inputs_missing_urls():
    """Verify input validation fails gracefully with clear error when URLs are missing."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": "wf_val_01",
        "analysis_id": str(uuid4()),
        "version_a": {"base_url": ""},
        "version_b": {"base_url": "http://localhost:3000"},
        "history": [],
    }

    res = await adapters.validate_inputs(state)
    assert res["status"] == WorkflowStatus.FAILED.value
    assert res["failure_type"] == FailureType.INVALID_INPUT.value
    assert "Version A base_url is required" in res["error_message"]
    assert len(res["history"]) == 1
    assert res["history"][0]["status"] == "FAILED"


@pytest.mark.asyncio
async def test_validate_inputs_success():
    """Verify input validation succeeds when valid URLs are provided."""
    adapters = InvestigationNodeAdapters()
    state: InvestigationWorkflowState = {
        "workflow_id": "wf_val_02",
        "analysis_id": str(uuid4()),
        "version_a": {"base_url": "http://localhost:3000"},
        "version_b": {"base_url": "http://localhost:3001"},
        "history": [],
    }

    res = await adapters.validate_inputs(state)
    assert res["status"] == WorkflowStatus.RUNNING.value
    assert res["current_phase"] == "validate_inputs"
    assert len(res["history"]) == 1
    assert res["history"][0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_finalize_no_regression():
    """Verify finalize_no_regression creates clean 0-regression suite."""
    adapters = InvestigationNodeAdapters()
    analysis_id = uuid4()
    state: InvestigationWorkflowState = {
        "workflow_id": "wf_fin_01",
        "analysis_id": str(analysis_id),
        "history": [],
    }

    res = await adapters.finalize_no_regression(state)
    assert res["status"] == WorkflowStatus.COMPLETED.value
    assert res["current_phase"] == "finalize_no_regression"
    assert res["investigation_suite"].summary.total_investigations == 0
    assert len(res["history"]) == 1
