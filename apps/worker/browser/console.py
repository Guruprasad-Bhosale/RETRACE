"""Deterministic Console and Page Error Observer."""

from datetime import UTC, datetime
from enum import StrEnum

from playwright.async_api import ConsoleMessage, Page
from playwright.async_api import Error as PlaywrightError
from pydantic import BaseModel, ConfigDict, Field

from apps.worker.browser.events import BrowserEventCollector, BrowserEventType


class ConsoleSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    LOG = "log"
    WARNING = "warning"
    ERROR = "error"


class ConsoleRecord(BaseModel):
    """Structured console or page error message."""

    model_config = ConfigDict(extra="forbid")

    severity: ConsoleSeverity
    text: str
    source_url: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    stack_trace: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    step_index: int = 0


class ConsoleObserver:
    """Attaches to a Playwright Page, capturing console logs and unhandled errors."""

    def __init__(self, event_collector: BrowserEventCollector | None = None) -> None:
        self.event_collector = event_collector
        self.records: list[ConsoleRecord] = []
        self.current_step_index: int = 0

    def attach(self, page: Page) -> None:
        """Attach listeners to the Playwright Page."""
        page.on("console", self._handle_console)
        page.on("pageerror", self._handle_page_error)

    def _normalize_severity(self, msg_type: str) -> ConsoleSeverity:
        t = msg_type.lower()
        if t in ("error", "assert"):
            return ConsoleSeverity.ERROR
        elif t in ("warn", "warning"):
            return ConsoleSeverity.WARNING
        elif t in ("info",):
            return ConsoleSeverity.INFO
        elif t in ("debug", "trace"):
            return ConsoleSeverity.DEBUG
        return ConsoleSeverity.LOG

    def _handle_console(self, msg: ConsoleMessage) -> None:
        severity = self._normalize_severity(msg.type)
        loc = msg.location
        url = loc.get("url") if loc else None
        line = loc.get("lineNumber") if loc else None
        col = loc.get("columnNumber") if loc else None

        record = ConsoleRecord(
            severity=severity,
            text=msg.text,
            source_url=url,
            line_number=line,
            column_number=col,
            step_index=self.current_step_index,
        )
        self.records.append(record)

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.CONSOLE,
                {
                    "severity": severity.value,
                    "text": msg.text,
                    "source_url": url,
                },
                step_index=self.current_step_index,
            )

    def _handle_page_error(self, error: PlaywrightError | Exception) -> None:
        error_msg = str(error)
        stack = getattr(error, "stack", None) or str(error)

        record = ConsoleRecord(
            severity=ConsoleSeverity.ERROR,
            text=error_msg,
            stack_trace=stack,
            step_index=self.current_step_index,
        )
        self.records.append(record)

        if self.event_collector:
            self.event_collector.emit(
                BrowserEventType.PAGE_ERROR,
                {
                    "error_text": error_msg,
                    "stack_trace": stack,
                },
                step_index=self.current_step_index,
            )

    def get_summary(self, step_index: int | None = None) -> dict[str, int]:
        """Return counts of errors and warnings."""
        target_records = (
            [r for r in self.records if r.step_index == step_index]
            if step_index is not None
            else self.records
        )
        errors = sum(1 for r in target_records if r.severity == ConsoleSeverity.ERROR)
        warnings = sum(1 for r in target_records if r.severity == ConsoleSeverity.WARNING)
        return {
            "console_errors_count": errors,
            "console_warnings_count": warnings,
        }

    def clear(self) -> None:
        """Reset records."""
        self.records.clear()
