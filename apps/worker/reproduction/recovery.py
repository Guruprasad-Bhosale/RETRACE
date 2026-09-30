"""Bounded Precondition Recovery for Deterministic Replay.

Hard Invariant:
Recovery may restore the expected precondition for an action (e.g. re-stabilization,
restoring prior state). Recovery may NEVER branch into alternative workflows or alter the causal experiment.
"""

import asyncio

from apps.worker.browser.session import BrowserSession
from apps.worker.reproduction.config import RecoveryPolicy
from apps.worker.reproduction.errors import RecoveryExhaustedError
from apps.worker.reproduction.models import ReproductionStep


class BoundedRecoveryManager:
    """Coordinates strict, bounded precondition restoration for transient replay desynchronization."""

    def __init__(self, policy: RecoveryPolicy) -> None:
        self.policy = policy
        self.recovery_attempts: int = 0

    def can_attempt_recovery(self) -> bool:
        """Check if remaining recovery quota allows an attempt."""
        return self.policy.enabled and self.recovery_attempts < self.policy.max_recovery_attempts

    async def restore_precondition(
        self,
        session: BrowserSession,
        step: ReproductionStep,
        expected_url: str | None = None,
    ) -> bool:
        """Attempt to restore the page precondition for the target step.

        Hard Invariant: Must not branch or execute unapproved exploratory actions.
        """
        if not self.can_attempt_recovery():
            raise RecoveryExhaustedError(
                f"Recovery exhausted ({self.recovery_attempts}/{self.policy.max_recovery_attempts} attempts used) for step {step.step_index}."
            )

        self.recovery_attempts += 1

        # 1. Bounded stabilization pause
        if self.policy.backtrack_delay_ms > 0:
            await asyncio.sleep(self.policy.backtrack_delay_ms / 1000.0)

        # 2. Re-stabilize DOM / network state via Phase 3 stabilizer
        try:
            await session.stabilizer.stabilize(session.page, step_index=step.step_index)
        except Exception:
            return False

        # 3. If expected_url was provided and page diverged, navigate directly to expected URL
        if expected_url and session.page.url != expected_url:
            try:
                await session.page.goto(expected_url, timeout=self.policy.backtrack_delay_ms * 2 + 5000)
                await session.stabilizer.stabilize(session.page, step_index=step.step_index)
            except Exception:
                return False

        return True
