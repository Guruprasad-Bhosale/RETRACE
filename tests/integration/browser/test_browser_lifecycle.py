"""Integration tests for BrowserManager lifecycle and context sandboxing."""

from uuid import uuid4

import pytest

from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_browser_manager_lifecycle(tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=config, storage=storage)

    # 1. Start browser
    await manager.start()
    assert manager._browser is not None
    assert manager._browser.is_connected()

    # 2. Create isolated session
    run_ctx = RunContext(
        analysis_id=uuid4(),
        version_id=uuid4(),
        run_id=uuid4(),
        trajectory_id=uuid4(),
    )

    async with manager.session(run_context=run_ctx) as session:
        # Navigate to data URL
        await session.page.set_content("<h1>Browser Test</h1><p>Running isolated session.</p>")
        obs = await session.initialize()

        assert obs.step_index == 0
        assert obs.state.page_title is not None or obs.state.url is not None
        assert obs.provenance.environment_context["browser_name"] == "chromium"
        assert len(obs.artifacts) > 0

    # 3. Stop browser
    await manager.stop()
    assert manager._browser is None
    assert manager._playwright is None
