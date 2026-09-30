"""Integration tests for seed navigation, state discovery, and state graph construction."""

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


mock_app = FastAPI()


@mock_app.get("/", response_class=HTMLResponse)
def home_view():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Mock App Home</title></head>
    <body>
        <h1>Home View</h1>
        <input id="search-box" name="search" placeholder="Search catalog..." />
        <a id="link-page-a" href="/page-a">Go to Page A</a>
        <a id="link-page-b" href="/page-b">Go to Page B</a>
    </body>
    </html>
    """


@mock_app.get("/page-a", response_class=HTMLResponse)
def page_a_view():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Mock App - Page A</title></head>
    <body>
        <h1>Page A View</h1>
        <button id="btn-action">Action on A</button>
        <a id="link-home" href="/">Return to Home</a>
    </body>
    </html>
    """


@mock_app.get("/page-b", response_class=HTMLResponse)
def page_b_view():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Mock App - Page B</title></head>
    <body>
        <h1>Page B View</h1>
        <a id="link-home" href="/">Return to Home</a>
    </body>
    </html>
    """


@pytest.fixture(scope="module")
def mock_server():
    port = get_free_port()
    server = uvicorn.Server(
        uvicorn.Config(app=mock_app, host="127.0.0.1", port=port, log_level="error")
    )
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    while not server.started:
        time.sleep(0.05)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.should_exit = True


@pytest.mark.asyncio
async def test_autonomous_explorer_state_graph_construction(mock_server, tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    b_config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=b_config, storage=storage)
    await manager.start()

    run_ctx = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
        name="Exploration-Integration-Test",
    )

    exp_config = ExplorationConfig(
        seed_url=f"{mock_server}/",
        max_steps=15,
        max_depth=4,
        max_actions_per_state=5,
    )

    try:
        async with manager.session(run_context=run_ctx) as session:
            explorer = AutonomousExplorer(config=exp_config, session=session)
            result = await explorer.explore()

            # Assert exploration discovered states and constructed graph
            assert result.states_discovered >= 3  # Root, Page A, Page B
            assert len(result.unique_routes) >= 3
            assert "/" in result.unique_routes
            assert "/page-a" in result.unique_routes
            assert "/page-b" in result.unique_routes
            assert result.transitions_count > 0
            assert result.successful_transitions > 0
            assert result.termination_reason in ("frontier_exhausted", "max_steps_reached")
            assert len(result.artifact_references) > 0

            # Verify diagnostic text formatter works
            from apps.worker.exploration.diagnostics import ExplorationDiagnosticsFormatter

            summary_text = ExplorationDiagnosticsFormatter.format_text_summary(result)
            assert "RETRACE AUTONOMOUS EXPLORATION SUMMARY" in summary_text
    finally:
        await manager.stop()
