"""Integration test verifying complete isolation between concurrent browser sessions."""

import asyncio
from uuid import uuid4

import pytest

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from packages.domain.models import ActionType
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_concurrent_sessions_strict_isolation(tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=config, storage=storage)
    await manager.start()

    run_ctx_a = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
        name="Run-A",
    )
    run_ctx_b = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
        name="Run-B",
    )

    try:
        async with manager.session(run_context=run_ctx_a) as session_a, manager.session(
            run_context=run_ctx_b
        ) as session_b:
            # HTML page testing storage and cookies
            test_html = """
            <!DOCTYPE html>
            <html>
            <head><title>Isolation Test</title></head>
            <body>
                <h1 id="title">Isolation</h1>
                <input id="inp" />
            </body>
            </html>
            """
            await session_a.page.set_content(test_html)
            await session_b.page.set_content(test_html)

            # Session A sets cookie in Context A
            await session_a.context.add_cookies(
                [{"name": "user_session", "value": "alice_session_token", "domain": "example.com", "path": "/"}]
            )

            # Session B sets cookie in Context B
            await session_b.context.add_cookies(
                [{"name": "user_session", "value": "bob_session_token", "domain": "example.com", "path": "/"}]
            )

            # Run parallel steps on Session A and Session B
            async def run_step_a():
                req = ExplicitActionRequest(
                    action_type=ActionType.TYPE,
                    target="css:#inp",
                    value="Alice Data",
                )
                return await session_a.step(req)

            async def run_step_b():
                req = ExplicitActionRequest(
                    action_type=ActionType.TYPE,
                    target="css:#inp",
                    value="Bob Data",
                )
                return await session_b.step(req)

            res_a, res_b = await asyncio.gather(run_step_a(), run_step_b())

            # Verify cookies remain strictly isolated
            cookies_a = await session_a.context.cookies("https://example.com")
            cookies_b = await session_b.context.cookies("https://example.com")

            cookie_map_a = {c["name"]: c["value"] for c in cookies_a}
            cookie_map_b = {c["name"]: c["value"] for c in cookies_b}

            assert cookie_map_a.get("user_session") == "alice_session_token"
            assert cookie_map_b.get("user_session") == "bob_session_token"

            # Verify artifact namespaces do NOT collide
            _, obs_a = res_a
            _, obs_b = res_b
            assert len(obs_a.artifacts) > 0
            assert len(obs_b.artifacts) > 0

            storage_uris_a = [a.storage_uri for a in obs_a.artifacts]
            storage_uris_b = [a.storage_uri for a in obs_b.artifacts]

            for uri in storage_uris_a:
                assert str(run_ctx_a.run_id) in uri
                assert str(run_ctx_b.run_id) not in uri

            for uri in storage_uris_b:
                assert str(run_ctx_b.run_id) in uri
                assert str(run_ctx_a.run_id) not in uri
    finally:
        await manager.stop()
