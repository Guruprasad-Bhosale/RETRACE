"""Integration tests for verified state backtracking and path replay."""

import socket
import threading
import time
from uuid import uuid4

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from apps.worker.browser.actions import ActionType, ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from apps.worker.exploration.backtracking import Backtracker
from apps.worker.exploration.state import ExplorationGraph, ExplorationState
from apps.worker.exploration.state_identity import StateIdentityCalculator
from apps.worker.exploration.transition import ExplorationTransition, compute_transition_id
from packages.storage.local import LocalDiskArtifactStorage


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


bt_app = FastAPI()


@bt_app.get("/", response_class=HTMLResponse)
def root_view():
    return """
    <html>
    <head><title>Backtrack Root</title></head>
    <body>
        <h1>Root View</h1>
        <a id="nav-step1" href="/step1">Step 1</a>
    </body>
    </html>
    """


@bt_app.get("/step1", response_class=HTMLResponse)
def step1_view():
    return """
    <html>
    <head><title>Backtrack Step 1</title></head>
    <body>
        <h1>Step 1 View</h1>
        <a id="nav-step2" href="/step2">Step 2</a>
    </body>
    </html>
    """


@bt_app.get("/step2", response_class=HTMLResponse)
def step2_view():
    return """
    <html>
    <head><title>Backtrack Step 2</title></head>
    <body>
        <h1>Step 2 View (Deep Branch)</h1>
    </body>
    </html>
    """


@pytest.fixture(scope="module")
def bt_server():
    port = get_free_port()
    server = uvicorn.Server(
        uvicorn.Config(app=bt_app, host="127.0.0.1", port=port, log_level="error")
    )
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    while not server.started:
        time.sleep(0.05)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.should_exit = True


@pytest.mark.asyncio
async def test_verified_backtracking_and_recovery(bt_server, tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    b_config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=b_config, storage=storage)
    await manager.start()

    run_ctx = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
    )

    try:
        async with manager.session(run_context=run_ctx) as session:
            # 1. Navigate to root
            req_0 = ExplicitActionRequest(action_type=ActionType.NAVIGATE, target=f"{bt_server}/")
            _, obs_0 = await session.step(req_0)
            id_0 = StateIdentityCalculator.calculate(obs_0).state_id

            graph = ExplorationGraph()
            state_0 = ExplorationState(state_id=id_0, observation_id=obs_0.id, url=obs_0.state.url, route="/")
            graph.add_state(state_0)

            # 2. Transition Root -> Step 1
            req_1 = ExplicitActionRequest(action_type=ActionType.CLICK, target="css:#nav-step1")
            act_res_1, obs_1 = await session.step(req_1)
            id_1 = StateIdentityCalculator.calculate(obs_1).state_id

            t1_id = compute_transition_id(id_0, ActionType.CLICK, "css:#nav-step1")
            trans_1 = ExplorationTransition(
                transition_id=t1_id,
                from_state_id=id_0,
                to_state_id=id_1,
                action_id=act_res_1.action.id,
                action_type=ActionType.CLICK,
                target="css:#nav-step1",
                target_identity="css:#nav-step1",
                observation_id=obs_1.id,
                success=True,
            )
            graph.record_transition(trans_1)
            state_1 = ExplorationState(
                state_id=id_1,
                observation_id=obs_1.id,
                url=obs_1.state.url,
                route="/step1",
                depth=1,
                parent_state_id=id_0,
                incoming_transition_id=t1_id,
            )
            graph.add_state(state_1)

            # 3. Transition Step 1 -> Step 2 (Deep Leaf)
            req_2 = ExplicitActionRequest(action_type=ActionType.CLICK, target="css:#nav-step2")
            act_res_2, obs_2 = await session.step(req_2)
            id_2 = StateIdentityCalculator.calculate(obs_2).state_id

            t2_id = compute_transition_id(id_1, ActionType.CLICK, "css:#nav-step2")
            trans_2 = ExplorationTransition(
                transition_id=t2_id,
                from_state_id=id_1,
                to_state_id=id_2,
                action_id=act_res_2.action.id,
                action_type=ActionType.CLICK,
                target="css:#nav-step2",
                target_identity="css:#nav-step2",
                observation_id=obs_2.id,
                success=True,
            )
            graph.record_transition(trans_2)
            state_2 = ExplorationState(
                state_id=id_2,
                observation_id=obs_2.id,
                url=obs_2.state.url,
                route="/step2",
                depth=2,
                parent_state_id=id_1,
                incoming_transition_id=t2_id,
            )
            graph.add_state(state_2)

            # 4. Now at Leaf (Step 2). Recover/backtrack to Step 1
            backtracker = Backtracker(graph=graph, seed_url=f"{bt_server}/")
            recovered_obs = await backtracker.recover_to_state(
                session=session,
                current_state_id=id_2,
                target_state_id=id_1,
            )

            rec_ident = StateIdentityCalculator.calculate(recovered_obs)
            assert rec_ident.state_id == id_1
            assert recovered_obs.state.url.endswith("/step1")

            # 5. Recover all the way back to Root State
            recovered_root = await backtracker.recover_to_state(
                session=session,
                current_state_id=id_1,
                target_state_id=id_0,
            )
            rec_root_ident = StateIdentityCalculator.calculate(recovered_root)
            assert rec_root_ident.state_id == id_0
    finally:
        await manager.stop()
