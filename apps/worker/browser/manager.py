"""Browser Lifecycle and Isolation Management Layer."""

import os
import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, Playwright, async_playwright

from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.errors import BrowserContextError, BrowserLaunchError
from apps.worker.browser.session import BrowserSession
from packages.storage.base import ArtifactStorage
from packages.storage.local import LocalDiskArtifactStorage


class BrowserManager:
    """Manages Playwright process lifecycle, browser sandboxing, and isolated session instantiation."""

    def __init__(
        self,
        default_config: BrowserConfig | None = None,
        storage: ArtifactStorage | None = None,
    ) -> None:
        self.default_config = default_config or BrowserConfig()
        self.storage = storage or LocalDiskArtifactStorage()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._browser_name: str = "chromium"
        self._browser_version: str = "unknown"

    async def start(self) -> None:
        """Launch Playwright and Chromium instance with secure sandbox defaults."""
        if self._browser is not None:
            return

        try:
            self._playwright = await async_playwright().start()
            self._browser_name = self.default_config.browser_type

            launch_options: dict[str, Any] = {
                "headless": self.default_config.headless,
            }

            match self.default_config.browser_type:
                case "chromium":
                    self._browser = await self._playwright.chromium.launch(**launch_options)
                case "firefox":
                    self._browser = await self._playwright.firefox.launch(**launch_options)
                case "webkit":
                    self._browser = await self._playwright.webkit.launch(**launch_options)
                case _:
                    self._browser = await self._playwright.chromium.launch(**launch_options)

            self._browser_version = self._browser.version
        except Exception as e:
            await self.stop()
            raise BrowserLaunchError(f"Failed to launch browser: {e}") from e

    async def create_session(
        self,
        run_context: RunContext,
        config: BrowserConfig | None = None,
    ) -> BrowserSession:
        """Create an isolated, ephemeral BrowserSession with fresh storage state and cookies."""
        if self._browser is None:
            await self.start()

        cfg = config or self.default_config
        temp_dir = tempfile.mkdtemp(prefix=f"retrace_run_{run_context.run_id.hex[:8]}_")

        try:
            context_options: dict[str, Any] = {
                "viewport": {
                    "width": cfg.viewport.width,
                    "height": cfg.viewport.height,
                },
                "device_scale_factor": cfg.device_scale_factor,
                "locale": cfg.locale,
                "timezone_id": cfg.timezone_id,
                "color_scheme": cfg.color_scheme,
                "reduced_motion": cfg.reduced_motion,
                "extra_http_headers": cfg.extra_http_headers,
            }

            if cfg.user_agent:
                context_options["user_agent"] = cfg.user_agent

            if cfg.har.enabled:
                har_path = os.path.join(temp_dir, f"har_{run_context.run_id}.har")
                context_options["record_har_path"] = har_path
                context_options["record_har_omit_content"] = cfg.har.omit_content

            # Create strictly isolated browser context
            assert self._browser is not None
            context = await self._browser.new_context(**context_options)

            # Start tracing if enabled
            if cfg.tracing.enabled:
                await context.tracing.start(
                    screenshots=cfg.tracing.screenshots,
                    snapshots=cfg.tracing.snapshots,
                    sources=cfg.tracing.sources,
                )

            page = await context.new_page()
            page.set_default_timeout(cfg.action_timeout_ms)
            page.set_default_navigation_timeout(cfg.navigation_timeout_ms)

            return BrowserSession(
                context=context,
                page=page,
                config=cfg,
                run_context=run_context,
                storage=self.storage,
                browser_name=self._browser_name,
                browser_version=self._browser_version,
                temp_dir=temp_dir,
            )

        except Exception as e:
            raise BrowserContextError(f"Failed to create isolated browser session: {e}") from e

    @asynccontextmanager
    async def session(
        self,
        run_context: RunContext,
        config: BrowserConfig | None = None,
    ) -> AsyncGenerator[BrowserSession, None]:
        """Async context manager guaranteeing session cleanup even on failure or unhandled exception."""
        sess = await self.create_session(run_context=run_context, config=config)
        try:
            yield sess
        finally:
            await sess.close()

    async def stop(self) -> None:
        """Close browser and stop Playwright process."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()
