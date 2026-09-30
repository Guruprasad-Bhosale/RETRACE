"""Integration test for end-to-end Version A vs Version B Commerce Lab exploration, alignment, semantic diff, and regression classification."""

import socket
import threading
import time
from uuid import uuid4

import pytest
import uvicorn

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.explorer import AutonomousExplorer
from apps.worker.regression.classifier import RegressionClassifier
from apps.worker.regression.diagnostics import RegressionDiagnosticsFormatter
from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2
from packages.storage.local import LocalDiskArtifactStorage


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def commerce_servers():
    """Start in-process Version A and Version B servers for autonomous exploration."""
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
async def test_commerce_exploration_alignment_diff_and_regression_classification(commerce_servers, tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    b_config = BrowserConfig(headless=True)
    manager = BrowserManager(default_config=b_config, storage=storage)
    await manager.start()

    v1_url = commerce_servers["v1_url"]
    v2_url = commerce_servers["v2_url"]

    analysis_id = uuid4()
    version_a_id = uuid4()
    version_b_id = uuid4()

    exp_config_a = ExplorationConfig(
        seed_url=f"{v1_url}/",
        max_steps=10,
        max_depth=3,
        max_actions_per_state=4,
    )
    exp_config_b = ExplorationConfig(
        seed_url=f"{v2_url}/",
        max_steps=10,
        max_depth=3,
        max_actions_per_state=4,
    )

    try:
        # 1. Explore Version A (Baseline)
        run_ctx_a = RunContext(
            analysis_id=analysis_id,
            version_id=version_a_id,
            run_id=uuid4(),
            trajectory_id=uuid4(),
            name="Explore-Commerce-VersionA",
        )
        async with manager.session(run_context=run_ctx_a) as session_a:
            explorer_a = AutonomousExplorer(config=exp_config_a, session=session_a)
            result_a = await explorer_a.explore()

        # 2. Explore Version B (Target)
        run_ctx_b = RunContext(
            analysis_id=analysis_id,
            version_id=version_b_id,
            run_id=uuid4(),
            trajectory_id=uuid4(),
            name="Explore-Commerce-VersionB",
        )
        async with manager.session(run_context=run_ctx_b) as session_b:
            explorer_b = AutonomousExplorer(config=exp_config_b, session=session_b)
            result_b = await explorer_b.explore()

        # 3. Behavioral Trajectory Alignment (Phase 5)
        align_config = AlignmentConfig(
            version_a_base_url=v1_url,
            version_b_base_url=v2_url,
        )
        aligner = TrajectoryAligner(config=align_config)
        alignment_result = aligner.align(result_a, result_b)

        # 4. Semantic Difference Analysis (Phase 6)
        diff_engine = SemanticDiffEngine()
        diff_result = diff_engine.compare(alignment_result)

        # 5. Regression Classification (Phase 7)
        classifier = RegressionClassifier()
        classification_result = classifier.classify(diff_result)

        # 6. Assertions on Classification Result
        assert classification_result.run_a_id == alignment_result.run_a_id
        assert classification_result.run_b_id == alignment_result.run_b_id
        assert classification_result.summary.total_differences_analyzed == len(diff_result.differences)

        # Verify classifications are stably sorted
        sort_keys = [c.deterministic_sort_key() for c in classification_result.classifications]
        assert sort_keys == sorted(sort_keys)

        # Format report and verify neutral unranked output
        summary_text = RegressionDiagnosticsFormatter.format_text_summary(classification_result)
        assert "RETRACE REGRESSION CLASSIFICATION REPORT" in summary_text
        assert "CLASSIFICATION SUMMARY COUNTS:" in summary_text

        # Ensure no forbidden vocabulary
        assert "severity" not in summary_text.lower()
        assert "critical" not in summary_text.lower()
        assert "root cause" not in summary_text.lower()
        assert "rank" not in summary_text.lower()

    finally:
        await manager.stop()
