"""Deterministic Page State Stabilization Module."""

import time
from typing import Any

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from apps.worker.browser.events import BrowserEventCollector, BrowserEventType


class StabilizationResult:
    """Outcome of a page stabilization cycle."""

    def __init__(
        self,
        success: bool,
        duration_ms: float,
        dom_settled: bool,
        network_settled: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.duration_ms = duration_ms
        self.dom_settled = dom_settled
        self.network_settled = network_settled
        self.details = details or {}


class Stabilizer:
    """Stabilizes page state using document readiness, DOM mutations, and network settling."""

    def __init__(
        self,
        event_collector: BrowserEventCollector | None = None,
        max_timeout_ms: float = 8000.0,
        settle_interval_ms: float = 100.0,
    ) -> None:
        self.event_collector = event_collector
        self.max_timeout_ms = max_timeout_ms
        self.settle_interval_ms = settle_interval_ms

    async def stabilize(
        self,
        page: Page,
        step_index: int = 0,
        timeout_ms: float | None = None,
    ) -> StabilizationResult:
        """Wait for page state, DOM stability, and network quiescence."""
        start_time = time.perf_counter()
        limit_ms = timeout_ms or self.max_timeout_ms
        dom_settled = False
        network_settled = False

        try:
            # 1. Ensure document is at least DOMContentLoaded / readyState
            await page.wait_for_load_state("domcontentloaded", timeout=limit_ms / 2)
        except (PlaywrightTimeoutError, Exception):
            pass

        # 2. Wait for DOM mutation settling via JavaScript evaluation
        try:
            # Inject a short mutation watcher or check document readyState
            dom_settled = await page.evaluate(
                """() => {
                    return new Promise((resolve) => {
                        let timeout;
                        const observer = new MutationObserver(() => {
                            clearTimeout(timeout);
                            timeout = setTimeout(() => {
                                observer.disconnect();
                                resolve(true);
                            }, 50);
                        });
                        observer.observe(document.body || document.documentElement, {
                            childList: true,
                            subtree: true,
                            attributes: true
                        });
                        // Safety timeout if no mutations happen immediately
                        timeout = setTimeout(() => {
                            observer.disconnect();
                            resolve(true);
                        }, 80);
                    });
                }"""
            )
        except Exception:
            dom_settled = True

        # 3. Controlled network settling (short timeout fallback, never hang)
        try:
            # Attempt a quick networkidle check with a strict short timeout
            quick_network_timeout = min(1500.0, limit_ms / 3)
            await page.wait_for_load_state("networkidle", timeout=quick_network_timeout)
            network_settled = True
        except (PlaywrightTimeoutError, Exception):
            # SPAs with open websockets or long polls will time out gracefully
            network_settled = False

        duration = max(0.0, (time.perf_counter() - start_time) * 1000.0)
        success = duration < limit_ms

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.STABILIZATION,
                {
                    "duration_ms": duration,
                    "dom_settled": dom_settled,
                    "network_settled": network_settled,
                },
                step_index=step_index,
            )

        return StabilizationResult(
            success=success,
            duration_ms=duration,
            dom_settled=dom_settled,
            network_settled=network_settled,
        )
