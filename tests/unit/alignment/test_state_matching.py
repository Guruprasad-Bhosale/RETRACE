"""Unit tests for StateMatcher."""

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.matcher import StateMatcher
from apps.worker.alignment.models import AlignmentRelation, EvidenceStrength, StateSignature


def test_state_matcher_exact_match() -> None:
    config = AlignmentConfig()
    sig_a = StateSignature(
        state_id="state-111",
        normalized_route="/cart",
        inventory_signature="inv-1",
        a11y_signature="a11y-1",
        ui_state_signature="ui-1",
    )
    sig_b = StateSignature(
        state_id="state-111",
        normalized_route="/cart",
        inventory_signature="inv-1",
        a11y_signature="a11y-1",
        ui_state_signature="ui-1",
    )

    relation, evidence = StateMatcher.match(sig_a, sig_b, config)
    assert relation == AlignmentRelation.EXACT_MATCH
    assert evidence.evidence_strength == EvidenceStrength.EXACT
    assert evidence.route_match is True


def test_state_matcher_strong_match_with_parent_and_action() -> None:
    config = AlignmentConfig()
    sig_a = StateSignature(
        state_id="state-aaa",
        normalized_route="/checkout",
        inventory_signature="inv-a",
        a11y_signature="a11y-a",
        ui_state_signature="ui-a",
    )
    sig_b = StateSignature(
        state_id="state-bbb",  # different state ID
        normalized_route="/checkout",
        inventory_signature="inv-b",
        a11y_signature="a11y-b",
        ui_state_signature="ui-b",
    )

    relation, evidence = StateMatcher.match(
        sig_a,
        sig_b,
        config,
        parent_match=True,
        action_match=True,
    )
    assert relation == AlignmentRelation.STRONG_MATCH
    assert evidence.evidence_strength == EvidenceStrength.STRONG
    assert evidence.parent_match is True
    assert evidence.action_match is True


def test_state_matcher_unmatched() -> None:
    config = AlignmentConfig()
    sig_a = StateSignature(
        state_id="state-1",
        normalized_route="/cart",
        inventory_signature="inv-1",
        a11y_signature="a11y-1",
        ui_state_signature="ui-1",
    )
    sig_b = StateSignature(
        state_id="state-2",
        normalized_route="/settings",
        inventory_signature="inv-2",
        a11y_signature="a11y-2",
        ui_state_signature="ui-2",
    )

    relation, evidence = StateMatcher.match(sig_a, sig_b, config)
    assert relation == AlignmentRelation.UNMATCHED
    assert evidence.evidence_strength == EvidenceStrength.NONE
