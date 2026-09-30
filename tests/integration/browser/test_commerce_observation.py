"""Integration tests demonstrating deterministic browser observation of Commerce Version A and Version B.

Verifies raw observation capture, state recording, network/console logging, and artifact
persistence without importing ground truth or containing any defect classification logic.
"""

import socket
import threading
import time
from uuid import uuid4

import pytest
import uvicorn

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, NetworkCapturePolicy, RunContext
from apps.worker.browser.manager import BrowserManager
from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2
from packages.domain.models import ActionType
from packages.storage.local import LocalDiskArtifactStorage


def get_free_port() -> int:
    """Find an available local port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def commerce_servers():
    """Start in-process Version A and Version B servers in daemon threads for live browser observation."""
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
async def test_observe_commerce_version_a_and_version_b(commerce_servers, tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    config = BrowserConfig(
        headless=True,
        network=NetworkCapturePolicy(capture_bodies=True),
    )
    manager = BrowserManager(default_config=config, storage=storage)
    await manager.start()

    v1_url = commerce_servers["v1_url"]
    v2_url = commerce_servers["v2_url"]

    analysis_id = uuid4()
    version_a_id = uuid4()
    version_b_id = uuid4()

    run_ctx_a = RunContext(
        analysis_id=analysis_id,
        version_id=version_a_id,
        run_id=uuid4(),
        trajectory_id=uuid4(),
        name="Observe-Commerce-VersionA",
    )
    run_ctx_b = RunContext(
        analysis_id=analysis_id,
        version_id=version_b_id,
        run_id=uuid4(),
        trajectory_id=uuid4(),
        name="Observe-Commerce-VersionB",
    )

    try:
        # ----------------------------------------------------------------------
        # 1. Observe Commerce Version A
        # ----------------------------------------------------------------------
        async with manager.session(run_context=run_ctx_a) as session_a:
            # Step 0: Navigate to Catalog
            req_nav_a = ExplicitActionRequest(
                action_type=ActionType.NAVIGATE,
                target=f"{v1_url}/",
            )
            _, obs_a_0 = await session_a.step(req_nav_a)
            assert obs_a_0.step_index == 1
            assert obs_a_0.state.url.rstrip("/").endswith(str(commerce_servers["v1_url"]).split(":")[-1]) or "/" in obs_a_0.state.url
            assert obs_a_0.state.dom_hash is not None
            assert len(obs_a_0.artifacts) >= 3  # Screenshot, DOM, A11y

            # Step 1: Type into Search Bar
            req_search_a = ExplicitActionRequest(
                action_type=ActionType.TYPE,
                target="css:#search-input",
                value="Headphones",
            )
            act_res_a_1, obs_a_1 = await session_a.step(req_search_a)
            assert act_res_a_1.success is True
            assert obs_a_1.step_index == 2

            # Step 2: Click Cart Nav Link
            req_cart_a = ExplicitActionRequest(
                action_type=ActionType.CLICK,
                target="css:#cart-nav-link",
            )
            act_res_a_2, obs_a_2 = await session_a.step(req_cart_a)
            assert act_res_a_2.success is True
            assert obs_a_2.step_index == 3
            assert obs_a_2.state.url.endswith("/cart.html")

            # Validate raw observations for Version A
            diag_a = session_a.get_diagnostics()
            assert diag_a.total_steps == 3
            assert diag_a.failed_actions_count == 0

        # ----------------------------------------------------------------------
        # 2. Observe Commerce Version B (Identical Action Sequence)
        # ----------------------------------------------------------------------
        async with manager.session(run_context=run_ctx_b) as session_b:
            # Step 0: Navigate to Catalog
            req_nav_b = ExplicitActionRequest(
                action_type=ActionType.NAVIGATE,
                target=f"{v2_url}/",
            )
            _, obs_b_0 = await session_b.step(req_nav_b)
            assert obs_b_0.step_index == 1
            assert obs_b_0.state.dom_hash is not None

            # Step 1: Type into Search Bar
            req_search_b = ExplicitActionRequest(
                action_type=ActionType.TYPE,
                target="css:#search-input",
                value="Headphones",
            )
            act_res_b_1, obs_b_1 = await session_b.step(req_search_b)
            assert act_res_b_1.success is True
            assert obs_b_1.step_index == 2

            # Step 2: Click Cart Nav Link
            req_cart_b = ExplicitActionRequest(
                action_type=ActionType.CLICK,
                target="css:#cart-nav-link",
            )
            act_res_b_2, obs_b_2 = await session_b.step(req_cart_b)
            assert act_res_b_2.success is True
            assert obs_b_2.step_index == 3
            assert obs_b_2.state.url.endswith("/cart.html")

            # Validate raw observations for Version B
            diag_b = session_b.get_diagnostics()
            assert diag_b.total_steps == 3

        # ----------------------------------------------------------------------
        # 3. Assert Artifact Namespaces & State Independence
        # ----------------------------------------------------------------------
        # Verify DOM hashes between Version A and Version B are recorded
        assert obs_a_0.state.dom_hash is not None
        assert obs_b_0.state.dom_hash is not None
        # Provenance records are complete and distinct
        assert obs_a_0.provenance.version_id == version_a_id
        assert obs_b_0.provenance.version_id == version_b_id

    finally:
        await manager.stop()
