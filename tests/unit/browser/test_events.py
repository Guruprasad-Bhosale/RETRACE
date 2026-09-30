"""Unit tests for monotonic event collection."""

from uuid import uuid4

from apps.worker.browser.events import BrowserEventCollector, BrowserEventType


def test_event_collector_monotonic_sequence():
    run_id = uuid4()
    traj_id = uuid4()
    collector = BrowserEventCollector(run_id=run_id, trajectory_id=traj_id)

    e0 = collector.emit(BrowserEventType.NAVIGATION, {"url": "http://a.com"}, step_index=0)
    e1 = collector.emit(BrowserEventType.REQUEST, {"url": "http://a.com/api"}, step_index=0)
    e2 = collector.emit(BrowserEventType.RESPONSE, {"status": 200}, step_index=0)
    e3 = collector.emit(BrowserEventType.ACTION_START, {"type": "click"}, step_index=1)

    assert e0.event_index == 0
    assert e1.event_index == 1
    assert e2.event_index == 2
    assert e3.event_index == 3

    assert collector.count() == 4
    events = collector.get_events()
    assert len(events) == 4
    assert [e.event_index for e in events] == [0, 1, 2, 3]


def test_event_collector_filter_and_clear():
    collector = BrowserEventCollector()
    collector.emit(BrowserEventType.NAVIGATION, {"url": "http://1"}, step_index=0)
    collector.emit(BrowserEventType.CONSOLE, {"text": "err"}, step_index=0)
    collector.emit(BrowserEventType.ACTION_START, {"target": "btn"}, step_index=1)

    step0_events = collector.get_events(step_index=0)
    assert len(step0_events) == 2

    step1_events = collector.get_events(step_index=1)
    assert len(step1_events) == 1

    collector.clear()
    assert collector.count() == 0
