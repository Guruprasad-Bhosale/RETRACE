"""Isolated Browser Session Coordinating Trajectory Progression and Multi-Modal Evidence."""

import os
import tempfile
import time

from playwright.async_api import BrowserContext, Page

from apps.worker.browser.a11y import AccessibilityObserver
from apps.worker.browser.actions import ActionExecutor, ActionResult, ExplicitActionRequest
from apps.worker.browser.artifacts import ArtifactCollector
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.console import ConsoleObserver
from apps.worker.browser.diagnostics import (
    DiagnosticFormatter,
    DiagnosticSummary,
    SensorTimingBreakdown,
)
from apps.worker.browser.dom import DOMObserver
from apps.worker.browser.events import BrowserEventCollector
from apps.worker.browser.inventory import ElementInventoryObserver
from apps.worker.browser.network import NetworkObserver
from apps.worker.browser.observation import ObservationBuilder
from apps.worker.browser.stabilization import Stabilizer
from packages.domain.models import Action, ArtifactReference, Observation
from packages.storage.base import ArtifactStorage


class BrowserSession:
    """Manages an isolated browser context, trajectory step progression, and evidence capture."""

    def __init__(
        self,
        context: BrowserContext,
        page: Page,
        config: BrowserConfig,
        run_context: RunContext,
        storage: ArtifactStorage,
        browser_name: str = "chromium",
        browser_version: str = "1.0",
        temp_dir: str | None = None,
    ) -> None:
        self.context = context
        self.page = page
        self.config = config
        self.run_context = run_context
        self.storage = storage
        self.browser_name = browser_name
        self.browser_version = browser_version
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="retrace_browser_")

        # Monotonic Event Stream
        self.events = BrowserEventCollector(
            run_id=self.run_context.run_id,
            trajectory_id=self.run_context.trajectory_id,
        )

        # Sensory Observers
        self.network = NetworkObserver(policy=config.network, event_collector=self.events)
        self.console = ConsoleObserver(event_collector=self.events)
        self.dom = DOMObserver()
        self.a11y = AccessibilityObserver()
        self.inventory = ElementInventoryObserver()
        self.stabilizer = Stabilizer(event_collector=self.events)

        # Artifacts & Actions
        self.artifacts = ArtifactCollector(storage=self.storage, run_context=self.run_context)
        self.actions_executor = ActionExecutor(run_context=self.run_context, event_collector=self.events)

        # Domain Observation Builder
        self.builder = ObservationBuilder(
            config=self.config,
            run_context=self.run_context,
            artifact_collector=self.artifacts,
            dom_observer=self.dom,
            a11y_observer=self.a11y,
            inventory_observer=self.inventory,
            network_observer=self.network,
            console_observer=self.console,
            browser_name=self.browser_name,
            browser_version=self.browser_version,
        )

        # Trajectory History & Diagnostics
        self.actions: list[Action] = []
        self.observations: list[Observation] = []
        self.step_timings: list[SensorTimingBreakdown] = []
        self.session_artifacts: list[ArtifactReference] = []
        self.current_step: int = 0
        self.session_start_time: float = time.perf_counter()

        # Attach page listeners
        self.network.attach(self.page)
        self.console.attach(self.page)

    async def initialize(self) -> Observation:
        """Stabilize initial page state, capture initial Observation (Step 0)."""
        step_start = time.perf_counter()
        stab_res = await self.stabilizer.stabilize(self.page, step_index=0)

        obs = await self.builder.build(
            page=self.page,
            step_index=0,
            prior_observation_id=None,
            caused_by_action_id=None,
            stabilization_result=stab_res,
        )
        self.observations.append(obs)

        total_ms = (time.perf_counter() - step_start) * 1000.0
        self.step_timings.append(
            SensorTimingBreakdown(
                step_index=0,
                action_execution_ms=0.0,
                stabilization_ms=stab_res.duration_ms,
                total_step_ms=total_ms,
            )
        )
        return obs

    async def step(self, action_request: ExplicitActionRequest) -> tuple[ActionResult, Observation]:
        """Execute an explicit action, progress trajectory step index, and capture resulting observation."""
        step_start = time.perf_counter()
        next_step = self.current_step + 1
        prior_obs = self.observations[-1] if self.observations else None
        prior_obs_id = prior_obs.id if prior_obs else None

        # 1. Execute explicit action
        self.network.current_step_index = next_step
        self.console.current_step_index = next_step
        action_res = await self.actions_executor.execute(
            page=self.page,
            request=action_request,
            step_index=next_step,
            prior_observation_id=prior_obs_id,
        )
        self.actions.append(action_res.action)

        # 2. Stabilize page
        stab_res = await self.stabilizer.stabilize(self.page, step_index=next_step)

        # 3. Capture Observation (standard or diagnostic on action failure)
        obs = await self.builder.build(
            page=self.page,
            step_index=next_step,
            prior_observation_id=prior_obs_id,
            caused_by_action_id=action_res.action.id,
            stabilization_result=stab_res,
            is_diagnostic=not action_res.success,
        )
        self.observations.append(obs)

        # Link resulting observation ID into domain Action
        action_res.action.resulting_observation_id = obs.id

        # Update step index
        self.current_step = next_step

        total_ms = (time.perf_counter() - step_start) * 1000.0
        self.step_timings.append(
            SensorTimingBreakdown(
                step_index=next_step,
                action_execution_ms=action_res.duration_ms,
                stabilization_ms=stab_res.duration_ms,
                total_step_ms=total_ms,
            )
        )

        return action_res, obs

    async def close(self) -> list[ArtifactReference]:
        """Finalize session-level traces/HAR archives, persist to storage, and close page."""
        # 1. Finalize Playwright Trace if enabled
        if self.config.tracing.enabled:
            trace_path = os.path.join(self.temp_dir, f"trace_{self.run_context.run_id}.zip")
            try:
                await self.context.tracing.stop(path=trace_path)
                if os.path.exists(trace_path):
                    with open(trace_path, "rb") as f:
                        trace_bytes = f.read()
                    ref = await self.artifacts.persist_trace_zip(trace_bytes)
                    self.session_artifacts.append(ref)
                    try:
                        os.remove(trace_path)
                    except Exception:
                        pass
            except Exception:
                pass

        # 2. Close page and context safely
        try:
            await self.page.close()
        except Exception:
            pass

        try:
            await self.context.close()
        except Exception:
            pass

        # 3. Check for HAR file if enabled
        if self.config.har.enabled:
            har_path = os.path.join(self.temp_dir, f"har_{self.run_context.run_id}.har")
            if os.path.exists(har_path):
                try:
                    with open(har_path, "rb") as f:
                        har_bytes = f.read()
                    ref = await self.artifacts.persist_session_har(har_bytes)
                    self.session_artifacts.append(ref)
                    os.remove(har_path)
                except Exception:
                    pass

        # Cleanup temporary directory
        try:
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

        return self.session_artifacts

    def get_diagnostics(self) -> DiagnosticSummary:
        """Produce structured diagnostic summary of the session."""
        total_duration = max(0.0, (time.perf_counter() - self.session_start_time) * 1000.0)
        return DiagnosticFormatter.generate_summary(
            analysis_id=str(self.run_context.analysis_id),
            version_id=str(self.run_context.version_id),
            run_id=str(self.run_context.run_id),
            trajectory_id=str(self.run_context.trajectory_id),
            actions=self.actions,
            observations=self.observations,
            events=self.events.get_events(),
            timings=self.step_timings,
            total_duration_ms=total_duration,
        )
