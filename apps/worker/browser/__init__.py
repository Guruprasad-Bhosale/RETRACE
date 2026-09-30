"""RETRACE Browser Observation Engine Package.

Provides a deterministic, multi-modal Playwright sensor for web application
exploration, state capture, interactive element inventory, and artifact persistence.
"""

from apps.worker.browser.actions import ActionExecutor, ActionResult, ExplicitActionRequest
from apps.worker.browser.artifacts import ArtifactCollector
from apps.worker.browser.config import (
    BrowserConfig,
    HarConfig,
    NetworkCapturePolicy,
    RunContext,
    ScreenshotConfig,
    TracingConfig,
    ViewportConfig,
)
from apps.worker.browser.diagnostics import (
    DiagnosticFormatter,
    DiagnosticSummary,
    SensorTimingBreakdown,
)
from apps.worker.browser.errors import (
    ActionExecutionError,
    ArtifactPersistenceError,
    BrowserContextError,
    BrowserCrashedError,
    BrowserEngineError,
    BrowserLaunchError,
    ElementNotFoundError,
    ElementNotInteractableError,
    NavigationFailedError,
    NavigationTimeoutError,
    StabilizationTimeoutError,
)
from apps.worker.browser.events import BrowserEvent, BrowserEventCollector, BrowserEventType
from apps.worker.browser.manager import BrowserManager
from apps.worker.browser.session import BrowserSession

__all__ = [
    "ActionExecutor",
    "ActionResult",
    "ActionExecutionError",
    "ArtifactCollector",
    "ArtifactPersistenceError",
    "BrowserConfig",
    "BrowserContextError",
    "BrowserCrashedError",
    "BrowserEngineError",
    "BrowserEvent",
    "BrowserEventCollector",
    "BrowserEventType",
    "BrowserLaunchError",
    "BrowserManager",
    "BrowserSession",
    "DiagnosticFormatter",
    "DiagnosticSummary",
    "ElementNotFoundError",
    "ElementNotInteractableError",
    "ExplicitActionRequest",
    "HarConfig",
    "NavigationFailedError",
    "NavigationTimeoutError",
    "NetworkCapturePolicy",
    "RunContext",
    "ScreenshotConfig",
    "SensorTimingBreakdown",
    "StabilizationTimeoutError",
    "TracingConfig",
    "ViewportConfig",
]
