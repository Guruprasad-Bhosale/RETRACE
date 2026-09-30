"""Integration tests for explicit deterministic browser action execution."""

from uuid import uuid4

import pytest

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from packages.domain.models import ActionType
from packages.storage.local import LocalDiskArtifactStorage

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Action Execution Test</title></head>
<body>
    <h1 id="heading">Test Page</h1>
    <button id="btn-submit" data-testid="submit-btn">Submit Order</button>
    <label for="username">Username</label>
    <input type="text" id="username" name="user" />
    <select id="country">
        <option value="US">United States</option>
        <option value="CA">Canada</option>
    </select>
    <div id="output" style="margin-top: 20px;">Initial</div>

    <script>
        document.getElementById('btn-submit').addEventListener('click', () => {
            document.getElementById('output').innerText = 'Clicked!';
        });
        document.getElementById('username').addEventListener('input', (e) => {
            document.getElementById('output').innerText = 'Typed: ' + e.target.value;
        });
        document.getElementById('country').addEventListener('change', (e) => {
            document.getElementById('output').innerText = 'Selected: ' + e.target.value;
        });
    </script>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_explicit_action_sequence_and_trajectory_progression(tmp_path):
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
            await session.page.set_content(SAMPLE_HTML)
            obs_0 = await session.initialize()
            assert obs_0.step_index == 0
            assert obs_0.prior_observation_id is None

            # Action 1: Type into input field
            req_type = ExplicitActionRequest(
                action_type=ActionType.TYPE,
                target="testid:username",
                value="alice",
            )
            act_res_1, obs_1 = await session.step(req_type)
            assert act_res_1.success is True
            assert act_res_1.action.step_index == 1
            assert obs_1.step_index == 1
            assert obs_1.prior_observation_id == obs_0.id
            assert obs_1.caused_by_action_id == act_res_1.action.id
            assert act_res_1.action.resulting_observation_id == obs_1.id

            # Action 2: Click button
            req_click = ExplicitActionRequest(
                action_type=ActionType.CLICK,
                target="testid:submit-btn",
            )
            act_res_2, obs_2 = await session.step(req_click)
            assert act_res_2.success is True
            assert act_res_2.action.step_index == 2
            assert obs_2.step_index == 2
            assert obs_2.prior_observation_id == obs_1.id
            assert obs_2.caused_by_action_id == act_res_2.action.id

            # Action 3: Select option
            req_select = ExplicitActionRequest(
                action_type=ActionType.SELECT,
                target="css:#country",
                value="CA",
            )
            act_res_3, obs_3 = await session.step(req_select)
            assert act_res_3.success is True
            assert act_res_3.action.step_index == 3
            assert obs_3.step_index == 3

            # Check output in page
            output_text = await session.page.inner_text("#output")
            assert output_text == "Selected: CA"

            # Check full diagnostics
            diag = session.get_diagnostics()
            assert diag.total_steps == 4  # 0, 1, 2, 3
            assert diag.actions_count == 3
            assert diag.failed_actions_count == 0
    finally:
        await manager.stop()
