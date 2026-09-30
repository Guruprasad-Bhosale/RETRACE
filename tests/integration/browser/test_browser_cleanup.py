"""Integration tests verifying reliable cleanup of browser resources, pages, and contexts."""

from uuid import uuid4

import pytest

from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_browser_cleanup_on_exception(tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=config, storage=storage)
    await manager.start()

    run_ctx = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
    )

    with pytest.raises(RuntimeError, match="Simulated worker crash"):
        async with manager.session(run_context=run_ctx) as session:
            await session.page.set_content("<h1>Crash Test</h1>")
            await session.initialize()
            raise RuntimeError("Simulated worker crash")

    # Verify context and page are cleaned up (manager remains usable for new sessions)
    run_ctx_2 = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
    )

    async with manager.session(run_context=run_ctx_2) as session_2:
        await session_2.page.set_content("<h1>Healthy Session</h1>")
        obs = await session_2.initialize()
        assert obs.step_index == 0

    await manager.stop()
