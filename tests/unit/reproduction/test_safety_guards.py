"""Unit Tests for Reproduction Safety Guards."""

from uuid import uuid4

import pytest

from apps.worker.reproduction.config import SafetyPolicy
from apps.worker.reproduction.errors import SafetyViolationError
from apps.worker.reproduction.models import ReproductionPath, ReproductionStep
from apps.worker.reproduction.safety import ReproductionSafetyGuard
from packages.domain.models import ActionType


def test_safety_guard_blocks_destructive_keywords():
    """Verify safety guard blocks dangerous operations like Place Order or Delete Account."""
    guard = ReproductionSafetyGuard(SafetyPolicy(block_destructive_actions=True))

    safe_step = ReproductionStep(
        step_index=1,
        action_type=ActionType.CLICK,
        accessible_name="Add to Cart",
        stable_target_identity="#add-cart",
    )
    safe, reason = guard.is_action_safe(safe_step)
    assert safe is True
    assert reason is None

    unsafe_step = ReproductionStep(
        step_index=2,
        action_type=ActionType.CLICK,
        accessible_name="Place Order",
        stable_target_identity="#place-order-btn",
    )
    safe, reason = guard.is_action_safe(unsafe_step)
    assert safe is False
    assert "place order" in reason.lower()


def test_safety_guard_blocks_disallowed_domain():
    """Verify safety guard rejects URLs not matching allowed domains."""
    policy = SafetyPolicy(allowed_domains=["localhost", "127.0.0.1"])
    guard = ReproductionSafetyGuard(policy)

    assert guard.is_url_allowed("http://localhost:3000/shop") is True
    assert guard.is_url_allowed("http://127.0.0.1:8000/api") is True
    assert guard.is_url_allowed("http://malicious-external.com/leak") is False


def test_safety_guard_validate_path_raises_exception():
    """Verify validate_path_safety raises SafetyViolationError for unsafe path."""
    guard = ReproductionSafetyGuard(SafetyPolicy(allowed_domains=["localhost"]))

    unsafe_path = ReproductionPath(
        path_id="path-unsafe",
        trajectory_id=uuid4(),
        classification_id="class-1",
        difference_id="diff-1",
        seed_url="http://external-hacker.com/",
        steps=[],
        path_signature="sig",
    )

    with pytest.raises(SafetyViolationError, match="not in allowed reproduction domains"):
        guard.validate_path_safety(unsafe_path)
