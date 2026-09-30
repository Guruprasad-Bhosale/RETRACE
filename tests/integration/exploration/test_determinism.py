"""Integration tests verifying deterministic decision-making across repeated exploration runs."""

import socket
import threading
import time
from uuid import uuid4

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.explorer import AutonomousExplorer
from packages.storage.local import LocalDiskArtifactStorage


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


det_app = FastAPI()


@det_app.get("/", response_class=HTMLResponse)
def det_root():
    return """
    <html>
    <head><title>Determinism Root</title></head>
    <body>
        <h1>Determinism Root</h1>
        <input id="q" name="search" placeholder="Search item..." />
        <a id="link-cat-1" href="/cat1">Category 1</a>
        <a id="link-cat-2" href="/cat2">Category 2</a>
        <button id="btn-info">View Info</button>
    </body>
    </html>
    """


@det_app.get("/cat1", response_class=HTMLResponse)
def det_cat1():
    return """
    <html>
    <head><title>Category 1</title></head>
    <body>
        <h1>Category 1</h1>
        <button id="btn-add">Add to list</button>
        <a id="link-root" href="/">Back</a>
    </body>
    </html>
    """


@det_app.get("/cat2", response_class=HTMLResponse)
def det_cat2():
    return """
    <html>
    <head><title>Category 2</title></head>
    <body>
        <h1>Category 2</h1>
        <a id="link-root" href="/">Back</a>
    </body>
    </html>
    """


@pytest.fixture(scope="module")
def det_server():
    port = get_free_port()
    server = uvicorn.Server(
        uvicorn.Config(app=det_app, host="127.0.0.1", port=port, log_level="error")
    )
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    while not server.started:
        time.sleep(0.05)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.should_exit = True


@pytest.mark.asyncio
async def test_exploration_determinism_across_multiple_runs(det_server, tmp_path):
    """Verify that two runs with identical configuration produce equivalent normalized decisions and graph topologies."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")

    b_config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=b_config, storage=storage)
    await manager.start()

    exp_config = ExplorationConfig(
        seed_url=f"{det_server}/",
        max_steps=12,
        max_depth=3,
        max_actions_per_state=4,
    )

    try:
        # ----------------------------------------------------------------------
        # Run 1
        # ----------------------------------------------------------------------
        run_ctx_1 = RunContext(
            analysis_id=uuid4(),
            version_id=uuid4(),
            run_id=uuid4(),
            trajectory_id=uuid4(),
            name="Run-1",
        )
        async with manager.session(run_context=run_ctx_1) as session_1:
            explorer_1 = AutonomousExplorer(config=exp_config, session=session_1)
            result_1 = await explorer_1.explore()

        # ----------------------------------------------------------------------
        # Run 2 (Identical Configuration)
        # ----------------------------------------------------------------------
        run_ctx_2 = RunContext(
            analysis_id=uuid4(),
            version_id=uuid4(),
            run_id=uuid4(),
            trajectory_id=uuid4(),
            name="Run-2",
        )
        async with manager.session(run_context=run_ctx_2) as session_2:
            explorer_2 = AutonomousExplorer(config=exp_config, session=session_2)
            result_2 = await explorer_2.explore()

        # ----------------------------------------------------------------------
        # Assert Deterministic Parity
        # ----------------------------------------------------------------------
        # 1. Same termination reason
        assert result_1.termination_reason == result_2.termination_reason

        # 2. Same total steps and states count
        assert result_1.total_steps == result_2.total_steps
        assert result_1.states_discovered == result_2.states_discovered
        assert result_1.transitions_count == result_2.transitions_count
        assert result_1.unique_routes == result_2.unique_routes

        # 3. Same state identity sequence
        state_ids_1 = [node["state_id"] for node in result_1.state_graph_nodes]
        state_ids_2 = [node["state_id"] for node in result_2.state_graph_nodes]
        assert state_ids_1 == state_ids_2

        # 4. Same transition sequence and actions
        transitions_1 = [
            (t["from_state_id"], t["action_type"], t["target_identity"], t["to_state_id"])
            for t in result_1.state_graph_edges
        ]
        transitions_2 = [
            (t["from_state_id"], t["action_type"], t["target_identity"], t["to_state_id"])
            for t in result_2.state_graph_edges
        ]
        assert transitions_1 == transitions_2
    finally:
        await manager.stop()
