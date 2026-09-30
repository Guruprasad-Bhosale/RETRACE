"""Unit tests for ActionMatcher."""

from apps.worker.alignment.matcher import ActionMatcher
from apps.worker.alignment.models import ActionSignature, AlignmentRelation, EvidenceStrength
from packages.domain.models import ActionType


def test_action_matcher_exact_match() -> None:
    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="testid:checkout-btn",
        accessible_name="Checkout",
        normalized_input_class=None,
    )
    sig_b = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="testid:checkout-btn",
        accessible_name="Checkout",
        normalized_input_class=None,
    )

    relation, evidence = ActionMatcher.match(sig_a, sig_b)
    assert relation == AlignmentRelation.EXACT_MATCH
    assert evidence.evidence_strength == EvidenceStrength.EXACT
    assert evidence.action_match is True
    assert "target:testid:checkout-btn" in evidence.matched_features


def test_action_matcher_strong_match_by_name_and_role() -> None:
    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn-1234",
        accessible_name="Checkout",
        target_role="button",
    )
    sig_b = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn-5678",
        accessible_name="Checkout",
        target_role="button",
    )

    relation, evidence = ActionMatcher.match(sig_a, sig_b)
    assert relation == AlignmentRelation.STRONG_MATCH
    assert evidence.evidence_strength == EvidenceStrength.STRONG


def test_action_matcher_type_mismatch() -> None:
    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn-1",
    )
    sig_b = ActionSignature(
        action_type=ActionType.TYPE,
        stable_target_identity="btn-1",
    )

    relation, evidence = ActionMatcher.match(sig_a, sig_b)
    assert relation == AlignmentRelation.UNMATCHED
    assert evidence.action_match is False
    assert "action_type" in evidence.mismatched_features
