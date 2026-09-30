"""Unit tests for workflow event emission and subscriptions."""

from uuid import uuid4

from apps.worker.orchestration.events import WorkflowEventBus
from apps.worker.orchestration.models import WorkflowEvent, WorkflowEventType


def test_event_bus_emission_and_listener_dispatch():
    """Verify event bus notifies listeners with structured events."""
    bus = WorkflowEventBus()
    received_events: list[WorkflowEvent] = []

    def on_event(event: WorkflowEvent) -> None:
        received_events.append(event)

    bus.subscribe(on_event)

    analysis_id = uuid4()
    bus.emit(
        event_type=WorkflowEventType.NODE_STARTED,
        workflow_id="wf_event_01",
        analysis_id=analysis_id,
        node_name="align",
        details={"version": "v1"},
    )

    assert len(received_events) == 1
    ev = received_events[0]
    assert ev.event_type == WorkflowEventType.NODE_STARTED
    assert ev.workflow_id == "wf_event_01"
    assert ev.analysis_id == analysis_id
    assert ev.node_name == "align"
    assert ev.details["version"] == "v1"

    # Test unsubscribe
    bus.unsubscribe(on_event)
    bus.emit(
        event_type=WorkflowEventType.NODE_COMPLETED,
        workflow_id="wf_event_01",
        analysis_id=analysis_id,
        node_name="align",
    )
    assert len(received_events) == 1  # Unsubscribed, so not received
