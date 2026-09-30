"""Unit tests for ActionSignature and ActionSignatureCalculator."""

from uuid import uuid4

from apps.worker.alignment.action_signature import ActionSignatureCalculator
from apps.worker.exploration.candidate import CandidateAction
from apps.worker.exploration.transition import ExplorationTransition
from packages.domain.models import Action, ActionType


def test_classify_input_value_classes() -> None:
    assert ActionSignatureCalculator.classify_input_value("user@test.org") == "EMAIL_VALUE"
    assert ActionSignatureCalculator.classify_input_value("123", name_hint="qty") == "NUMBER_VALUE"
    assert ActionSignatureCalculator.classify_input_value("shoes", name_hint="search_query") == "SEARCH_VALUE"
    assert ActionSignatureCalculator.classify_input_value("555-0199", name_hint="phone") == "TEL_VALUE"
    assert ActionSignatureCalculator.classify_input_value("2026-09-21") == "DATE_VALUE"
    assert ActionSignatureCalculator.classify_input_value("random text") == "TEXT_VALUE"
    assert ActionSignatureCalculator.classify_input_value(None) is None


def test_action_signature_from_candidate() -> None:
    cand = CandidateAction(
        candidate_id="cand-1",
        action_type=ActionType.CLICK,
        target="testid:checkout-btn",
        stable_element_id="testid:checkout-btn",
        source_state_id="state-1",
        source_observation_id=uuid4(),
        document_order=0,
        metadata={"tag": "button", "accessible_name": "Checkout"},
    )
    sig = ActionSignatureCalculator.from_candidate(cand)
    assert sig.action_type == ActionType.CLICK
    assert sig.stable_target_identity == "testid:checkout-btn"
    assert sig.accessible_name == "Checkout"
    assert sig.target_role == "button"
    assert "type=click|target=testid:checkout-btn" in sig.compute_signature_hash()


def test_action_signature_from_transition() -> None:
    trans = ExplorationTransition(
        transition_id="trans-1",
        from_state_id="s1",
        to_state_id="s2",
        action_id=uuid4(),
        action_type=ActionType.TYPE,
        target="input#email",
        target_identity="input#email",
        value="test@example.com",
        observation_id=uuid4(),
        success=True,
    )
    sig = ActionSignatureCalculator.from_transition(trans)
    assert sig.action_type == ActionType.TYPE
    assert sig.normalized_input_class == "EMAIL_VALUE"


def test_action_signature_from_action() -> None:
    act = Action(
        session_id=uuid4(),
        version_id=uuid4(),
        trajectory_id=uuid4(),
        step_index=1,
        action_type=ActionType.CLICK,
        selector="button#submit",
    )
    sig = ActionSignatureCalculator.from_action(act, {"accessible_name": "Submit", "tag": "button"})
    assert sig.action_type == ActionType.CLICK
    assert sig.accessible_name == "Submit"
