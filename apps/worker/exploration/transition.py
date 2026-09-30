"""Deterministic Transition Identity and Edge Transition Recording Module."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ActionType


def compute_transition_id(
    from_state_id: str,
    action_type: ActionType | str,
    stable_target_identity: str,
    normalized_input: str | None = None,
) -> str:
    """Generate a deterministic transition identifier for loop prevention and graph edge tracking."""
    act_str = action_type.value if isinstance(action_type, ActionType) else str(action_type)
    val_str = normalized_input or ""
    raw = f"{from_state_id}|{act_str}|{stable_target_identity}|{val_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ExplorationTransition(BaseModel):
    """Immutable record of an exploration transition edge between application states."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str
    from_state_id: str
    to_state_id: str
    action_id: UUID
    action_type: ActionType
    target: str
    target_identity: str
    value: str | None = None
    observation_id: UUID
    success: bool
    error_message: str | None = None
    duration_ms: float = 0.0
    step_index: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
