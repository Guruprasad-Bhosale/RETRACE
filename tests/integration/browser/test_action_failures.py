"""Integration tests for failed action observation semantics and resilient diagnostic capture."""

from uuid import uuid4

import pytest

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from packages.domain.models import ActionType
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_failed_action_captures_diagnostic_observation_and_preserves_state(tmp_path):
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

    try:
        async with manager.session(run_context=run_ctx) as session:
            await session.page.set_content(
                """
                <html>
                <head><title>Failure Diagnostic Test</title></head>
                <body>
                    <h1>Page Loaded</h1>
                    <button id="existing-btn">Valid Button</button>
                </body>
                </html>
                """
            )
            obs_0 = await session.initialize()
            assert obs_0.step_index == 0

            # Step 1: Attempt action on non-existent element
            req_failed = ExplicitActionRequest(
                action_type=ActionType.CLICK,
                target="testid:non-existent-button-999",
                timeout_ms=1000.0,
            )
            act_res, obs_1 = await session.step(req_failed)

            # Assert failed action was recorded accurately
            assert act_res.success is False
            assert act_res.error_type is not None
            assert act_res.action.metadata["success"] is False

            # Assert diagnostic observation was captured and linked
            assert obs_1.step_index == 1
            assert obs_1.caused_by_action_id == act_res.action.id
            assert obs_1.prior_observation_id == obs_0.id
            assert obs_1.provenance.metadata["is_diagnostic"] is True
            assert obs_1.state.summary["is_diagnostic"] is True
            assert len(obs_1.artifacts) > 0

            # Assert session is STILL alive and can perform subsequent valid actions
            req_valid = ExplicitActionRequest(
                action_type=ActionType.CLICK,
                target="css:#existing-btn",
            )
            act_res_2, obs_2 = await session.step(req_valid)
            assert act_res_2.success is True
            assert obs_2.step_index == 2
            assert obs_2.prior_observation_id == obs_1.id

            diag = session.get_diagnostics()
            assert diag.total_steps == 3
            assert diag.actions_count == 2
            assert diag.failed_actions_count == 1
    finally:
        await manager.stop()
