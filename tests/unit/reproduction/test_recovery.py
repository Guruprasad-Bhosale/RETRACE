"""Unit Tests for Bounded Precondition Recovery."""

import pytest

from apps.worker.reproduction.config import RecoveryPolicy
from apps.worker.reproduction.errors import RecoveryExhaustedError
from apps.worker.reproduction.models import ReproductionStep
from apps.worker.reproduction.recovery import BoundedRecoveryManager
from packages.domain.models import ActionType


def test_recovery_quota_enforcement():
    """Verify recovery manager honors max_recovery_attempts limit."""
    policy = RecoveryPolicy(enabled=True, max_recovery_attempts=1)
    manager = BoundedRecoveryManager(policy)

    assert manager.can_attempt_recovery() is True
    manager.recovery_attempts = 1
    assert manager.can_attempt_recovery() is False


def test_recovery_disabled_policy():
    """Verify recovery manager immediately rejects attempts when disabled."""
    policy = RecoveryPolicy(enabled=False, max_recovery_attempts=2)
    manager = BoundedRecoveryManager(policy)
    assert manager.can_attempt_recovery() is False


@pytest.mark.asyncio
async def test_recovery_exhausted_error():
    """Verify calling restore_precondition when quota is exhausted raises RecoveryExhaustedError."""
    policy = RecoveryPolicy(enabled=True, max_recovery_attempts=0)
    manager = BoundedRecoveryManager(policy)

    step = ReproductionStep(
        step_index=1,
        action_type=ActionType.CLICK,
        stable_target_identity="#btn",
    )

    with pytest.raises(RecoveryExhaustedError, match="Recovery exhausted"):
        await manager.restore_precondition(session=None, step=step)  # type: ignore
