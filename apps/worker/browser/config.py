"""RETRACE Browser Observation Engine Configuration.

Provides strongly typed configuration for browser execution, timeouts,
viewports, network capture policies, tracing, and execution run contexts.
"""

import os
import platform
import sys
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ViewportConfig(BaseModel):
    """Viewport dimensions and device metrics."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=240, le=2160)


class TracingConfig(BaseModel):
    """Playwright session tracing configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    screenshots: bool = True
    snapshots: bool = True
    sources: bool = False


class HarConfig(BaseModel):
    """HAR network recording configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    omit_content: bool = True


class ScreenshotConfig(BaseModel):
    """Screenshot capture configuration."""

    model_config = ConfigDict(extra="forbid")

    full_page: bool = False
    image_type: Literal["png", "jpeg"] = "png"
    quality: int | None = Field(default=None, ge=1, le=100)


class NetworkCapturePolicy(BaseModel):
    """Policy governing request/response body interception and sanitization."""

    model_config = ConfigDict(extra="forbid")

    # Network body capture MUST be disabled by default unless explicitly enabled
    capture_bodies: bool = False
    max_body_bytes: int = Field(default=65536, ge=0, le=1048576)  # 64 KB default limit
    allowed_content_types: list[str] = Field(
        default_factory=lambda: [
            "application/json",
            "application/problem+json",
            "text/plain",
            "text/html",
            "application/x-www-form-urlencoded",
        ]
    )
    redact_headers: list[str] = Field(
        default_factory=lambda: [
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "proxy-authorization",
            "x-auth-token",
            "api-key",
        ]
    )
    redact_query_params: list[str] = Field(
        default_factory=lambda: [
            "token",
            "access_token",
            "refresh_token",
            "auth",
            "key",
            "api_key",
            "apikey",
            "secret",
            "password",
            "pwd",
            "session_id",
        ]
    )
    redact_body_fields: list[str] = Field(
        default_factory=lambda: [
            "password",
            "pwd",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "apikey",
            "credit_card",
            "card_number",
            "cvv",
            "ssn",
        ]
    )


class BrowserConfig(BaseModel):
    """Strongly typed browser execution configuration."""

    model_config = ConfigDict(extra="forbid")

    headless: bool = True
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    viewport: ViewportConfig = Field(default_factory=ViewportConfig)
    device_scale_factor: float = Field(default=1.0, ge=0.5, le=4.0)
    default_timeout_ms: float = Field(default=15000.0, ge=100.0, le=120000.0)
    navigation_timeout_ms: float = Field(default=20000.0, ge=100.0, le=180000.0)
    action_timeout_ms: float = Field(default=10000.0, ge=100.0, le=60000.0)
    locale: str = "en-US"
    timezone_id: str = "UTC"
    user_agent: str | None = None
    color_scheme: Literal["light", "dark", "no-preference"] = "light"
    reduced_motion: Literal["reduce", "no-preference"] = "no-preference"
    extra_http_headers: dict[str, str] = Field(default_factory=dict)
    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
    har: HarConfig = Field(default_factory=HarConfig)
    network: NetworkCapturePolicy = Field(default_factory=NetworkCapturePolicy)


class RunContext(BaseModel):
    """Explicit Execution / Run boundary coordinating a BrowserSession."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: UUID
    version_id: UUID
    run_id: UUID = Field(default_factory=uuid4)
    trajectory_id: UUID = Field(default_factory=uuid4)
    name: str = Field(default="Run-0")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def artifact_namespace(self, relative_path: str = "") -> str:
        """Construct isolated artifact storage key namespace."""
        base = (
            f"analyses/{self.analysis_id}/versions/{self.version_id}/"
            f"runs/{self.run_id}/trajectories/{self.trajectory_id}"
        )
        if relative_path:
            clean = relative_path.lstrip("/")
            return f"{base}/{clean}"
        return base


def get_environment_provenance(browser_name: str, browser_version: str) -> dict[str, Any]:
    """Capture deterministic environment metadata for reproducible runs."""
    import importlib.metadata

    try:
        pw_version = importlib.metadata.version("playwright")
    except Exception:
        pw_version = "unknown"

    return {
        "browser_name": browser_name,
        "browser_version": browser_version,
        "playwright_version": pw_version,
        "os_platform": sys.platform,
        "os_release": platform.platform(),
        "python_version": sys.version.split()[0],
        "node_environment": os.environ.get("NODE_ENV", "production"),
    }
