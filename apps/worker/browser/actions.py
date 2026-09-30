"""Explicit Deterministic Action Execution Module."""

import time
from typing import Any, Literal
from uuid import UUID, uuid4

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel, ConfigDict, Field

from apps.worker.browser.config import RunContext
from apps.worker.browser.errors import (
    ActionExecutionError,
    ElementNotFoundError,
    NavigationFailedError,
)
from apps.worker.browser.events import BrowserEventCollector, BrowserEventType
from packages.domain.models import Action, ActionType, utc_now


class ExplicitActionRequest(BaseModel):
    """Specification for an explicit deterministic browser action."""

    model_config = ConfigDict(extra="forbid")

    action_type: ActionType
    target: str | None = None
    target_strategy: Literal["auto", "testid", "role", "label", "text", "css", "url"] = "auto"
    value: str | None = None
    coordinates: tuple[float, float] | None = None
    timeout_ms: float = 10000.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    """Execution outcome of a browser action."""

    model_config = ConfigDict(extra="forbid")

    action: Action
    success: bool
    duration_ms: float
    before_url: str
    after_url: str
    error_type: str | None = None
    error_message: str | None = None
    target_resolved: str | None = None


class ActionExecutor:
    """Executes deterministic actions on a Playwright Page."""

    def __init__(
        self,
        run_context: RunContext,
        event_collector: BrowserEventCollector | None = None,
    ) -> None:
        self.run_context = run_context
        self.event_collector = event_collector

    def _resolve_locator(
        self, page: Page, target: str, strategy: str = "auto"
    ) -> tuple[Locator, str]:
        """Resolve locator based on target string and preferred strategy."""
        if not target:
            raise ElementNotFoundError("No target specified for action")

        strat = strategy.lower()
        if strat == "testid" or target.startswith("testid:"):
            tid = target.split(":", 1)[1] if target.startswith("testid:") else target
            return page.locator(f'[data-testid="{tid}"], [data-test="{tid}"], [id="{tid}"]'), f"testid:{tid}"

        if strat == "label" or target.startswith("label:"):
            lbl = target.split(":", 1)[1] if target.startswith("label:") else target
            return page.get_by_label(lbl, exact=False), f"label:{lbl}"

        if strat == "text" or target.startswith("text:"):
            txt = target.split(":", 1)[1] if target.startswith("text:") else target
            return page.get_by_text(txt, exact=False), f"text:{txt}"

        if strat == "role" or target.startswith("role:"):
            role_spec = target.split(":", 1)[1] if target.startswith("role:") else target
            # e.g. button[name='Submit']
            if "[" in role_spec and "]" in role_spec:
                role_name = role_spec.split("[")[0].strip()
                name_part = role_spec.split("[")[1].rstrip("]").replace("name=", "").strip("'\"")
                return page.get_by_role(role_name, name=name_part), f"role:{role_name}[name='{name_part}']"
            return page.get_by_role(role_spec), f"role:{role_spec}"

        # Default CSS selector fallback
        clean_target = target.split(":", 1)[1] if target.startswith("css:") else target
        return page.locator(clean_target), f"css:{clean_target}"

    async def execute(
        self,
        page: Page,
        request: ExplicitActionRequest,
        step_index: int,
        prior_observation_id: UUID | None = None,
    ) -> ActionResult:
        """Execute a single explicit action and record domain Action entity."""
        before_url = page.url
        start_time = time.perf_counter()
        target_resolved_desc = None
        action_id = uuid4()

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.ACTION_START,
                {
                    "action_type": request.action_type.value,
                    "target": request.target,
                    "value": request.value,
                },
                step_index=step_index,
            )

        success = True
        error_type = None
        error_message = None

        try:
            match request.action_type:
                case ActionType.NAVIGATE:
                    if not request.target:
                        raise NavigationFailedError("No URL specified for NAVIGATE action")
                    target_resolved_desc = request.target
                    await page.goto(
                        request.target,
                        timeout=request.timeout_ms,
                        wait_until="domcontentloaded",
                    )

                case ActionType.CLICK:
                    locator, target_resolved_desc = self._resolve_locator(
                        page, request.target or "", request.target_strategy
                    )
                    count = await locator.count()
                    if count == 0:
                        raise ElementNotFoundError(f"No elements matched target: {request.target}")
                    first_loc = locator.first
                    await first_loc.click(timeout=request.timeout_ms)

                case ActionType.TYPE:
                    locator, target_resolved_desc = self._resolve_locator(
                        page, request.target or "", request.target_strategy
                    )
                    count = await locator.count()
                    if count == 0:
                        raise ElementNotFoundError(f"No elements matched target: {request.target}")
                    first_loc = locator.first
                    await first_loc.fill(request.value or "", timeout=request.timeout_ms)

                case ActionType.SELECT:
                    locator, target_resolved_desc = self._resolve_locator(
                        page, request.target or "", request.target_strategy
                    )
                    count = await locator.count()
                    if count == 0:
                        raise ElementNotFoundError(f"No elements matched target: {request.target}")
                    first_loc = locator.first
                    await first_loc.select_option(value=request.value, timeout=request.timeout_ms)

                case ActionType.HOVER:
                    locator, target_resolved_desc = self._resolve_locator(
                        page, request.target or "", request.target_strategy
                    )
                    count = await locator.count()
                    if count == 0:
                        raise ElementNotFoundError(f"No elements matched target: {request.target}")
                    first_loc = locator.first
                    await first_loc.hover(timeout=request.timeout_ms)

                case ActionType.SCROLL:
                    if request.target:
                        locator, target_resolved_desc = self._resolve_locator(
                            page, request.target, request.target_strategy
                        )
                        first_loc = locator.first
                        await first_loc.scroll_into_view_if_needed(timeout=request.timeout_ms)
                    elif request.coordinates:
                        x, y = request.coordinates
                        await page.mouse.wheel(x, y)
                    else:
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")

                case ActionType.WAIT:
                    wait_ms = float(request.value or 1000.0)
                    target_resolved_desc = f"wait:{wait_ms}ms"
                    await page.wait_for_timeout(wait_ms)

                case ActionType.PRESS_KEY:
                    key = request.value or "Enter"
                    target_resolved_desc = f"key:{key}"
                    if request.target:
                        locator, _ = self._resolve_locator(page, request.target, request.target_strategy)
                        await locator.first.press(key, timeout=request.timeout_ms)
                    else:
                        await page.keyboard.press(key)

                case _:
                    raise ActionExecutionError(f"Unsupported action type: {request.action_type}")

        except PlaywrightTimeoutError as e:
            success = False
            error_type = "TimeoutError"
            error_message = f"Action timed out after {request.timeout_ms}ms: {e}"
        except ActionExecutionError as e:
            success = False
            error_type = e.__class__.__name__
            error_message = str(e)
        except Exception as e:
            success = False
            error_type = e.__class__.__name__
            error_message = f"Unexpected action failure: {e}"

        duration_ms = max(0.0, (time.perf_counter() - start_time) * 1000.0)
        after_url = page.url

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.ACTION_END,
                {
                    "action_type": request.action_type.value,
                    "success": success,
                    "duration_ms": duration_ms,
                    "error": error_message,
                },
                step_index=step_index,
            )

        # Build Phase 1 domain Action entity
        domain_action = Action(
            id=action_id,
            session_id=self.run_context.analysis_id,
            version_id=self.run_context.version_id,
            trajectory_id=self.run_context.trajectory_id,
            step_index=step_index,
            action_type=request.action_type,
            selector=request.target,
            value=request.value,
            coordinates=request.coordinates,
            duration_ms=duration_ms,
            prior_observation_id=prior_observation_id,
            resulting_observation_id=None,  # Linked following next observation
            timestamp=utc_now(),
            metadata={
                "target_strategy": request.target_strategy,
                "target_resolved": target_resolved_desc,
                "success": success,
                "error_type": error_type,
                "error_message": error_message,
                "before_url": before_url,
                "after_url": after_url,
                "run_id": str(self.run_context.run_id),
            },
        )

        return ActionResult(
            action=domain_action,
            success=success,
            duration_ms=duration_ms,
            before_url=before_url,
            after_url=after_url,
            error_type=error_type,
            error_message=error_message,
            target_resolved=target_resolved_desc,
        )
