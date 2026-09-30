"""Unit tests for BrowserConfig and RunContext."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.worker.browser.config import (
    BrowserConfig,
    RunContext,
    ViewportConfig,
    get_environment_provenance,
)


def test_browser_config_defaults():
    config = BrowserConfig()
    assert config.headless is True
    assert config.browser_type == "chromium"
    assert config.viewport.width == 1280
    assert config.viewport.height == 720
    assert config.default_timeout_ms == 15000.0
    assert config.network.capture_bodies is False  # Disabled by default
    assert config.tracing.enabled is False
    assert config.har.enabled is False


def test_browser_config_validation():
    with pytest.raises(ValidationError):
        # Viewport width too small
        BrowserConfig(viewport=ViewportConfig(width=100, height=720))

    with pytest.raises(ValidationError):
        # Action timeout too small
        BrowserConfig(action_timeout_ms=5.0)


def test_run_context_artifact_namespace():
    analysis_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    traj_id = uuid4()

    ctx = RunContext(
        analysis_id=analysis_id,
        version_id=version_id,
        run_id=run_id,
        trajectory_id=traj_id,
        name="TestRun",
    )

    ns = ctx.artifact_namespace("screenshot.png")
    expected = f"analyses/{analysis_id}/versions/{version_id}/runs/{run_id}/trajectories/{traj_id}/screenshot.png"
    assert ns == expected


def test_environment_provenance_structure():
    prov = get_environment_provenance("chromium", "120.0.0.0")
    assert prov["browser_name"] == "chromium"
    assert prov["browser_version"] == "120.0.0.0"
    assert "playwright_version" in prov
    assert "os_platform" in prov
    assert "python_version" in prov
