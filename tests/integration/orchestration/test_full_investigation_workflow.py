"""Integration test for full investigation workflow execution via runner."""

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import MemorySaver

from apps.worker.orchestration.models import (
    InvestigationRequest,
    VersionConfig,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner


@pytest.mark.asyncio
async def test_full_investigation_workflow_runner():
    checkpointer = MemorySaver()
    runner = InvestigationWorkflowRunner(checkpointer=checkpointer)

    req = InvestigationRequest(
        project_id=uuid4(),
        version_a=VersionConfig(
            version_id=uuid4(),
            name="v1",
            base_url="http://invalid-runner-test-url-1",
        ),
        version_b=VersionConfig(
            version_id=uuid4(),
            name="v2",
            base_url="http://invalid-runner-test-url-2",
        ),
    )

    wf_id = await runner.start_investigation(req)
    assert wf_id is not None

    status_info = runner.get_status(wf_id)
    assert status_info is not None
    assert "workflow_id" in status_info
    assert status_info["workflow_id"] == wf_id
