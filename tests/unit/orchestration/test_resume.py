"""Unit tests for resuming workflow executions."""

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import MemorySaver

from apps.worker.orchestration.models import (
    InvestigationRequest,
    VersionConfig,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner


@pytest.mark.asyncio
async def test_runner_resume_unstarted_workflow():
    checkpointer = MemorySaver()
    runner = InvestigationWorkflowRunner(checkpointer=checkpointer)

    # Resuming a workflow that does not exist in memory or checkpointer returns None
    result = await runner.resume_workflow("non-existent-wf")
    assert result is None


@pytest.mark.asyncio
async def test_runner_start_and_status():
    checkpointer = MemorySaver()
    runner = InvestigationWorkflowRunner(checkpointer=checkpointer)

    req = InvestigationRequest(
        project_id=uuid4(),
        version_a=VersionConfig(
            version_id=uuid4(),
            name="v1",
            base_url="http://invalid-url-for-quick-fail-1",
        ),
        version_b=VersionConfig(
            version_id=uuid4(),
            name="v2",
            base_url="http://invalid-url-for-quick-fail-2",
        ),
    )

    wf_id = await runner.start_investigation(req)
    assert wf_id is not None

    status_info = runner.get_status(wf_id)
    assert status_info is not None
    assert "status" in status_info
