"""Deterministic Event Collection Module with Monotonic Sequencing."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrowserEventType(StrEnum):
    NAVIGATION = "navigation"
    FRAME_NAVIGATED = "frame_navigated"
    REQUEST = "request"
    RESPONSE = "response"
    REQUEST_FAILED = "request_failed"
    CONSOLE = "console"
    PAGE_ERROR = "page_error"
    DIALOG = "dialog"
    CRASH = "crash"
    ACTION_START = "action_start"
    ACTION_END = "action_end"
    STABILIZATION = "stabilization"


class BrowserEvent(BaseModel):
    """Immutable, monotonically sequenced browser event."""

    model_config = ConfigDict(extra="forbid")

    event_index: int = Field(ge=0, description="Strict monotonically increasing sequence number")
    event_type: BrowserEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_id: UUID | None = None
    trajectory_id: UUID | None = None
    step_index: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class BrowserEventCollector:
    """Thread-safe / async monotonic event collector for a browser session."""

    def __init__(self, run_id: UUID | None = None, trajectory_id: UUID | None = None) -> None:
        self.run_id = run_id
        self.trajectory_id = trajectory_id
        self._sequence: int = 0
        self._events: list[BrowserEvent] = []

    def emit(
        self,
        event_type: BrowserEventType,
        payload: dict[str, Any],
        step_index: int = 0,
    ) -> BrowserEvent:
        """Record an event with next monotonic sequence index."""
        current_idx = self._sequence
        self._sequence += 1
        event = BrowserEvent(
            event_index=current_idx,
            event_type=event_type,
            run_id=self.run_id,
            trajectory_id=self.trajectory_id,
            step_index=step_index,
            payload=payload,
        )
        self._events.append(event)
        return event

    def get_events(self, step_index: int | None = None) -> list[BrowserEvent]:
        """Return all events, or events filtered by step index."""
        if step_index is not None:
            return [e for e in self._events if e.step_index == step_index]
        return list(self._events)

    def count(self) -> int:
        """Return total number of events recorded."""
        return len(self._events)

    def clear(self) -> None:
        """Reset event stream."""
        self._events.clear()
        self._sequence = 0
