"""Unit tests for accessibility observer, inventory, errors, and diagnostics."""

from uuid import uuid4

from apps.worker.browser.a11y import AccessibilityObserver
from apps.worker.browser.diagnostics import DiagnosticFormatter, SensorTimingBreakdown
from apps.worker.browser.errors import (
    ActionExecutionError,
    BrowserEngineError,
    ElementNotFoundError,
)
from apps.worker.browser.events import BrowserEvent, BrowserEventType
from apps.worker.browser.inventory import ActionableElement, ElementBoundingBox, ElementInventory
from packages.domain.models import (
    Action,
    ActionType,
    ApplicationStateSnapshot,
    Observation,
    Provenance,
)


def test_a11y_hash_deterministic():
    text = "- heading 'Home' [level=1]\n- button 'Checkout'"
    h1 = AccessibilityObserver.compute_hash(text)
    h2 = AccessibilityObserver.compute_hash(text)
    assert h1 == h2
    assert len(h1) == 64


def test_element_inventory_model():
    bbox = ElementBoundingBox(x=10.0, y=20.0, width=100.0, height=30.0)
    el = ActionableElement(
        tag="button",
        role="button",
        accessible_name="Submit",
        test_id="submit-btn",
        is_visible=True,
        is_enabled=True,
        bounding_box=bbox,
        stable_identity="testid:submit-btn",
        selector_candidates=['[data-testid="submit-btn"]', 'role=button[name="Submit"]'],
    )
    inv = ElementInventory(elements=[el], total_count=1, by_tag={"button": 1})
    assert inv.total_count == 1
    assert inv.elements[0].stable_identity == "testid:submit-btn"


def test_error_hierarchy_serialization():
    err = ElementNotFoundError("Element not found", details={"target": "#checkout-btn"})
    assert isinstance(err, ActionExecutionError)
    assert isinstance(err, BrowserEngineError)
    d = err.to_dict()
    assert d["error_type"] == "ElementNotFoundError"
    assert d["details"]["target"] == "#checkout-btn"


def test_diagnostic_formatter():
    aid = uuid4()
    vid = uuid4()
    rid = uuid4()
    tid = uuid4()

    action = Action(
        session_id=aid,
        version_id=vid,
        trajectory_id=tid,
        step_index=1,
        action_type=ActionType.CLICK,
        selector="#btn",
        metadata={"success": True},
    )

    state = ApplicationStateSnapshot(url="http://test.com")
    prov = Provenance(analysis_id=aid, version_id=vid, trajectory_id=tid)
    obs = Observation(
        session_id=aid,
        version_id=vid,
        trajectory_id=tid,
        step_index=1,
        state=state,
        provenance=prov,
    )

    ev = BrowserEvent(event_index=0, event_type=BrowserEventType.NAVIGATION, payload={})
    timing = SensorTimingBreakdown(step_index=1, total_step_ms=120.5)

    summary = DiagnosticFormatter.generate_summary(
        analysis_id=str(aid),
        version_id=str(vid),
        run_id=str(rid),
        trajectory_id=str(tid),
        actions=[action],
        observations=[obs],
        events=[ev],
        timings=[timing],
        total_duration_ms=150.0,
    )

    assert summary.total_steps == 1
    assert summary.actions_count == 1
    text_report = DiagnosticFormatter.format_text_report(summary)
    assert "RETRACE BROWSER SENSOR DIAGNOSTIC REPORT" in text_report
    assert str(rid) in text_report
