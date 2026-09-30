"""Structured Event Emission & Subscription for Workflow Execution."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from apps.worker.orchestration.models import (
    WorkflowEvent,
    WorkflowEventType,
    utc_now,
)

EventListener = Callable[[WorkflowEvent], None]


class WorkflowEventBus:
    """Thread-safe in-process event bus for workflow monitoring."""

    def __init__(self) -> None:
        self._listeners: list[EventListener] = []

    def subscribe(self, listener: EventListener) -> None:
        """Register an event listener callback."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: EventListener) -> None:
        """Unregister an event listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(
        self,
        event_type: WorkflowEventType,
        workflow_id: str,
        analysis_id: UUID | str,
        node_name: str | None = None,
        attempt: int = 1,
        details: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """Emit a structured event to all registered listeners."""
        parsed_analysis_id = (
            analysis_id if isinstance(analysis_id, UUID) else UUID(str(analysis_id))
        )
        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            analysis_id=parsed_analysis_id,
            node_name=node_name,
            attempt=attempt,
            timestamp=utc_now(),
            details=details or {},
        )
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                # Event listeners must not break workflow execution
                pass
        return event


# Global default event bus
default_event_bus = WorkflowEventBus()
