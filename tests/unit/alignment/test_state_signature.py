"""Unit tests for StateSignature and StateSignatureCalculator."""

from uuid import uuid4

from apps.worker.alignment.state_signature import StateSignatureCalculator
from apps.worker.exploration.state import ExplorationState
from packages.domain.models import ApplicationStateSnapshot, Observation, Provenance


def test_state_signature_clean_title() -> None:
    assert StateSignatureCalculator.clean_title("(2) RETRACE Store") == "RETRACE Store"
    assert StateSignatureCalculator.clean_title("RETRACE Store") == "RETRACE Store"
    assert StateSignatureCalculator.clean_title(None) == ""


def test_state_signature_from_exploration_state() -> None:
    st = ExplorationState(
        state_id="state-abc",
        observation_id=uuid4(),
        url="http://localhost:3001/checkout?session_id=123",
        route="/checkout",
        depth=1,
    )
    sig = StateSignatureCalculator.from_exploration_state(st)
    assert sig.state_id == "state-abc"
    assert sig.normalized_route == "/checkout"


def test_state_signature_from_observation() -> None:
    obs = Observation(
        session_id=uuid4(),
        version_id=uuid4(),
        trajectory_id=uuid4(),
        step_index=1,
        provenance=Provenance(analysis_id=uuid4(), version_id=uuid4()),
        state=ApplicationStateSnapshot(
            url="http://localhost:3001/cart",
            dom_hash="dom123",
            a11y_tree_hash="a11y123",
            http_status=200,
            page_title="(1) Cart",
            interactive_elements_count=5,
            summary={"inventory_breakdown": {"button": 2, "a": 3}},
        ),
    )
    sig = StateSignatureCalculator.from_observation(obs)
    assert sig.normalized_route == "/cart"
    assert sig.observational.http_status == 200
    assert sig.observational.page_title == "Cart"
    assert sig.observational.interactive_elements_count == 5
