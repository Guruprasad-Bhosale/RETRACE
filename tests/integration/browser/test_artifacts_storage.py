"""Integration tests for multi-modal artifact persistence, Tracing, and HAR lifecycle."""

from uuid import uuid4

import pytest

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, HarConfig, RunContext, TracingConfig
from apps.worker.browser.manager import BrowserManager
from packages.domain.models import ActionType, ArtifactKind
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_session_traces_har_and_artifacts_storage_lifecycle(tmp_path):
    storage_dir = tmp_path / "artifacts"
    storage = LocalDiskArtifactStorage(base_dir=storage_dir)

    # Enable tracing and HAR at session level
    config = BrowserConfig(
        headless=True,
        tracing=TracingConfig(enabled=True),
        har=HarConfig(enabled=True),
    )
    manager = BrowserManager(default_config=config, storage=storage)
    await manager.start()

    run_ctx = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
    )

    try:
        session = await manager.create_session(run_context=run_ctx, config=config)
        await session.page.set_content(
            """
            <html>
            <head><title>Artifacts & Tracing Test</title></head>
            <body>
                <h1>Artifacts Check</h1>
                <button id="btn">Click me</button>
            </body>
            </html>
            """
        )
        obs_0 = await session.initialize()

        # Check observation artifacts (screenshot, dom, a11y)
        kinds = {a.kind for a in obs_0.artifacts}
        assert ArtifactKind.SCREENSHOT in kinds
        assert ArtifactKind.DOM_SNAPSHOT in kinds
        assert ArtifactKind.A11Y_TREE in kinds

        # Verify artifacts exist on storage
        for art in obs_0.artifacts:
            assert art.sha256_hash is not None
            assert art.size_bytes > 0
            # Retrieve from storage
            key = art.metadata["storage_key"]
            stored_bytes = await storage.get(key)
            assert len(stored_bytes) == art.size_bytes

        # Execute one action
        req = ExplicitActionRequest(action_type=ActionType.CLICK, target="css:#btn")
        await session.step(req)

        # Close session and verify session-level Trace and HAR artifacts
        session_artifacts = await session.close()
        assert len(session_artifacts) >= 2  # Playwright Trace + HAR

        session_kinds = {a.kind for a in session_artifacts}
        assert ArtifactKind.PLAYWRIGHT_TRACE in session_kinds
        assert ArtifactKind.HAR_TRACE in session_kinds

        # Verify trace artifact is readable from storage
        trace_ref = next(a for a in session_artifacts if a.kind == ArtifactKind.PLAYWRIGHT_TRACE)
        trace_data = await storage.get(trace_ref.metadata["storage_key"])
        assert len(trace_data) > 0
    finally:
        await manager.stop()
