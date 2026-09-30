"""Deterministic Observation Builder and Domain Assembler."""

from typing import Any
from uuid import UUID, uuid4

from playwright.async_api import Page

from apps.worker.browser.a11y import AccessibilityObserver
from apps.worker.browser.artifacts import ArtifactCollector
from apps.worker.browser.config import BrowserConfig, RunContext, get_environment_provenance
from apps.worker.browser.console import ConsoleObserver
from apps.worker.browser.dom import DOMObserver
from apps.worker.browser.inventory import ElementInventoryObserver
from apps.worker.browser.network import NetworkObserver
from apps.worker.browser.stabilization import StabilizationResult
from packages.domain.models import (
    ApplicationStateSnapshot,
    ArtifactReference,
    Observation,
    Provenance,
    utc_now,
)


class ObservationBuilder:
    """Orchestrates DOM, accessibility, inventory, network, and console sensors into a Phase 1 Observation."""

    def __init__(
        self,
        config: BrowserConfig,
        run_context: RunContext,
        artifact_collector: ArtifactCollector,
        dom_observer: DOMObserver,
        a11y_observer: AccessibilityObserver,
        inventory_observer: ElementInventoryObserver,
        network_observer: NetworkObserver,
        console_observer: ConsoleObserver,
        browser_name: str = "chromium",
        browser_version: str = "1.0",
    ) -> None:
        self.config = config
        self.run_context = run_context
        self.artifact_collector = artifact_collector
        self.dom_observer = dom_observer
        self.a11y_observer = a11y_observer
        self.inventory_observer = inventory_observer
        self.network_observer = network_observer
        self.console_observer = console_observer
        self.browser_name = browser_name
        self.browser_version = browser_version

    async def build(
        self,
        page: Page,
        step_index: int,
        prior_observation_id: UUID | None = None,
        caused_by_action_id: UUID | None = None,
        stabilization_result: StabilizationResult | None = None,
        is_diagnostic: bool = False,
    ) -> Observation:
        """Capture page state, persist artifacts, and construct an immutable Observation domain entity."""
        obs_id = uuid4()
        current_url = page.url
        page_title = None
        try:
            page_title = await page.title()
        except Exception:
            pass

        # 1. Capture DOM
        dom_snapshot = None
        try:
            dom_snapshot = await self.dom_observer.capture(page)
        except Exception:
            pass

        # 2. Capture Accessibility
        a11y_snapshot = None
        try:
            a11y_snapshot = await self.a11y_observer.capture(page)
        except Exception:
            pass

        # 3. Capture Element Inventory
        inventory = None
        try:
            inventory = await self.inventory_observer.capture(page)
        except Exception:
            pass

        # 4. Capture Screenshot
        screenshot_bytes = None
        try:
            screenshot_bytes = await page.screenshot(
                full_page=self.config.screenshot.full_page,
                type=self.config.screenshot.image_type,
            )
        except Exception:
            pass

        # 5. Summarize Network & Console metrics for this step
        net_summary = self.network_observer.get_summary(step_index=step_index)
        console_summary = self.console_observer.get_summary(step_index=step_index)

        # 6. Persist Artifacts via ArtifactCollector
        artifacts: list[ArtifactReference] = []

        if screenshot_bytes:
            try:
                ref = await self.artifact_collector.persist_screenshot(
                    screenshot_bytes=screenshot_bytes,
                    step_index=step_index,
                    is_full_page=self.config.screenshot.full_page,
                )
                artifacts.append(ref)
            except Exception as e:
                print(f"[ERROR] persist_screenshot failed: {e}")

        if dom_snapshot:
            try:
                ref = await self.artifact_collector.persist_dom_html(
                    html_content=dom_snapshot.normalized_html,
                    step_index=step_index,
                )
                artifacts.append(ref)
            except Exception as e:
                print(f"[ERROR] persist_dom_html failed: {e}")

        if a11y_snapshot:
            try:
                ref = await self.artifact_collector.persist_a11y_tree(
                    a11y_content=a11y_snapshot.aria_snapshot_yaml,
                    step_index=step_index,
                )
                artifacts.append(ref)
            except Exception as e:
                print(f"[ERROR] persist_a11y_tree failed: {e}")

        # Console logs for this step
        step_console_records = [
            r.model_dump() for r in self.console_observer.records if r.step_index == step_index
        ]
        if step_console_records:
            try:
                ref = await self.artifact_collector.persist_console_log(
                    console_records=step_console_records,
                    step_index=step_index,
                )
                artifacts.append(ref)
            except Exception:
                pass

        # Network records for this step
        step_net_records = [
            r.model_dump() for r in self.network_observer.records if r.step_index == step_index
        ]
        if step_net_records:
            try:
                ref = await self.artifact_collector.persist_network_log(
                    network_records=step_net_records,
                    step_index=step_index,
                )
                artifacts.append(ref)
            except Exception:
                pass

        # 7. Environment Context for Deterministic Provenance
        env_context = get_environment_provenance(self.browser_name, self.browser_version)
        env_context.update(
            {
                "viewport": {
                    "width": self.config.viewport.width,
                    "height": self.config.viewport.height,
                },
                "device_scale_factor": self.config.device_scale_factor,
                "locale": self.config.locale,
                "timezone_id": self.config.timezone_id,
                "color_scheme": self.config.color_scheme,
                "reduced_motion": self.config.reduced_motion,
                "user_agent": self.config.user_agent or "default",
            }
        )

        provenance = Provenance(
            analysis_id=self.run_context.analysis_id,
            version_id=self.run_context.version_id,
            trajectory_id=self.run_context.trajectory_id,
            step_index=step_index,
            collected_at=utc_now(),
            collector_service="retrace-browser-sensor",
            environment_context=env_context,
            metadata={
                "run_id": str(self.run_context.run_id),
                "is_diagnostic": is_diagnostic,
                "a11y_api_used": a11y_snapshot.api_used if a11y_snapshot else "none",
            },
        )

        # 8. Assemble ApplicationStateSnapshot
        state_summary: dict[str, Any] = {
            "dom_node_count": dom_snapshot.node_count if dom_snapshot else 0,
            "element_counts": dom_snapshot.element_counts if dom_snapshot else {},
            "inventory_breakdown": inventory.by_tag if inventory else {},
            "stabilization": (
                {
                    "duration_ms": stabilization_result.duration_ms,
                    "dom_settled": stabilization_result.dom_settled,
                    "network_settled": stabilization_result.network_settled,
                }
                if stabilization_result
                else None
            ),
            "is_diagnostic": is_diagnostic,
        }

        # Determine last HTTP response status for this step if available
        last_http_status = None
        if step_net_records:
            responses = [r["status_code"] for r in step_net_records if r.get("status_code")]
            if responses:
                last_http_status = responses[-1]

        state = ApplicationStateSnapshot(
            url=current_url,
            page_title=page_title,
            http_status=last_http_status,
            viewport={"width": self.config.viewport.width, "height": self.config.viewport.height},
            dom_hash=dom_snapshot.dom_hash if dom_snapshot else None,
            a11y_tree_hash=a11y_snapshot.a11y_hash if a11y_snapshot else None,
            console_errors_count=console_summary["console_errors_count"],
            console_warnings_count=console_summary["console_warnings_count"],
            network_requests_count=net_summary["total_requests"],
            network_failures_count=net_summary["failed_requests"],
            latency_ms=net_summary["avg_latency_ms"],
            interactive_elements_count=inventory.total_count if inventory else 0,
            summary=state_summary,
        )

        return Observation(
            id=obs_id,
            session_id=self.run_context.analysis_id,
            version_id=self.run_context.version_id,
            trajectory_id=self.run_context.trajectory_id,
            step_index=step_index,
            state=state,
            artifacts=artifacts,
            provenance=provenance,
            prior_observation_id=prior_observation_id,
            caused_by_action_id=caused_by_action_id,
            timestamp=utc_now(),
        )
