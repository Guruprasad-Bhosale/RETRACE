"""Unit tests for state identity projection and transition identity calculation."""

from uuid import uuid4

from apps.worker.exploration.state_identity import StateIdentityCalculator
from apps.worker.exploration.transition import compute_transition_id
from packages.domain.models import (
    ActionType,
    ApplicationStateSnapshot,
    Observation,
    Provenance,
)


def test_state_identity_normalizes_volatile_params_and_routes():
    # Different volatile query parameters should produce the same normalized route
    url_1 = "http://example.com/cart.html?category=audio&_t=123456789&timestamp=999"
    url_2 = "http://example.com/cart.html?_t=987654321&category=audio"

    route_1 = StateIdentityCalculator.normalize_route(url_1)
    route_2 = StateIdentityCalculator.normalize_route(url_2)

    assert route_1 == "/cart.html?category=audio"
    assert route_2 == "/cart.html?category=audio"
    assert route_1 == route_2


def test_state_identity_deterministic_hash():
    aid = uuid4()
    vid = uuid4()
    tid = uuid4()

    state = ApplicationStateSnapshot(
        url="http://example.com/catalog",
        page_title="RETRACE Catalog",
        a11y_tree_hash="a11y_hash_123",
        interactive_elements_count=5,
        summary={"inventory_breakdown": {"button": 2, "input": 3}},
    )
    obs = Observation(
        session_id=aid,
        version_id=vid,
        trajectory_id=tid,
        step_index=0,
        state=state,
        provenance=Provenance(analysis_id=aid, version_id=vid, trajectory_id=tid),
    )

    ident_1 = StateIdentityCalculator.calculate(obs)
    ident_2 = StateIdentityCalculator.calculate(obs)

    assert ident_1.state_id == ident_2.state_id
    assert len(ident_1.state_id) == 64


def test_transition_id_uniqueness_and_determinism():
    state_a = "state_aaa"
    t1 = compute_transition_id(state_a, ActionType.CLICK, "btn:checkout", None)
    t2 = compute_transition_id(state_a, ActionType.CLICK, "btn:checkout", None)
    t3 = compute_transition_id(state_a, ActionType.TYPE, "inp:query", "test")

    assert t1 == t2
    assert t1 != t3
