"""End-to-End Integration Test for LangGraph Investigation Workflow on Commerce Lab."""

import socket
import threading
import time
from uuid import uuid4

import pytest
import uvicorn

from apps.worker.browser.config import BrowserConfig
from apps.worker.browser.manager import BrowserManager
from apps.worker.orchestration.models import (
    InvestigationRequest,
    ResourceBudget,
    VersionConfig,
    WorkflowStatus,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2
from packages.storage.local import LocalDiskArtifactStorage


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def commerce_servers():
    """Start in-process Version A and Version B servers for end-to-end pipeline execution."""
    port_v1 = get_free_port()
    port_v2 = get_free_port()

    server_v1 = uvicorn.Server(
        uvicorn.Config(app=app_v1, host="127.0.0.1", port=port_v1, log_level="error")
    )
    server_v2 = uvicorn.Server(
        uvicorn.Config(app=app_v2, host="127.0.0.1", port=port_v2, log_level="error")
    )

    t1 = threading.Thread(target=server_v1.run, daemon=True)
    t2 = threading.Thread(target=server_v2.run, daemon=True)
    t1.start()
    t2.start()

    while not server_v1.started or not server_v2.started:
        time.sleep(0.05)

    base_url_v1 = f"http://127.0.0.1:{port_v1}"
    base_url_v2 = f"http://127.0.0.1:{port_v2}"

    yield {"v1_url": base_url_v1, "v2_url": base_url_v2}

    server_v1.should_exit = True
    server_v2.should_exit = True


@pytest.mark.asyncio
async def test_commerce_lab_langgraph_workflow_e2e(commerce_servers, tmp_path):
    """Verify full end-to-end investigation workflow through LangGraph orchestration."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "orchestration_artifacts")
    b_config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=b_config, storage=storage)
    await manager.start()

    v1_url = commerce_servers["v1_url"]
    v2_url = commerce_servers["v2_url"]
    analysis_id = uuid4()

    req = InvestigationRequest(
        project_id="commerce-lab-orchestration",
        analysis_id=analysis_id,
        version_a=VersionConfig(
            base_url=v1_url,
            repository_path="lab/applications/commerce/v1",
        ),
        version_b=VersionConfig(
            base_url=v2_url,
            repository_path="lab/applications/commerce/v2",
        ),
        budget=ResourceBudget(
            max_exploration_steps=8,
            max_reproduction_attempts=2,
        ),
    )

    runner = InvestigationWorkflowRunner(
        storage=storage,
        browser_manager=manager,
    )

    try:
        result_state = await runner.run(req)

        if result_state.get("status") == WorkflowStatus.FAILED.value:
            print("ERROR MESSAGE:", result_state.get("error_message"))
            print("HISTORY:", result_state.get("history"))

        assert result_state["status"] in [
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.INCONCLUSIVE.value,
        ], f"Workflow failed with error: {result_state.get('error_message')}"
        assert result_state["investigation_suite"] is not None
        suite = result_state["investigation_suite"]

        assert suite.analysis_id == analysis_id
        assert len(suite.investigations) > 0

        # Verify first investigation package integrity
        inv = suite.investigations[0]
        assert inv.investigation_id is not None
        assert inv.report is not None
        assert len(inv.report.sections) == 11

        if inv.generated_test:
            assert "import { test, expect } from '@playwright/test';" in inv.generated_test.generated_source

        # Verify node execution history
        history = result_state.get("history", [])
        executed_nodes = [h["node_name"] for h in history]
        assert "validate_inputs" in executed_nodes
        assert "prepare_versions" in executed_nodes
        assert "explore" in executed_nodes
        assert "align" in executed_nodes
        assert "diff" in executed_nodes
        assert "classify" in executed_nodes
        assert "reproduce" in executed_nodes
        assert "root_cause" in executed_nodes
        assert "assemble" in executed_nodes
        assert "finalize" in executed_nodes

    finally:
        await manager.stop()
