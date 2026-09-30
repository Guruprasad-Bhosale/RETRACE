"""Deterministic Action Signature Module.

Extracts normalized signatures for actions across Version A and Version B.
Normalizes target identity, role, accessible name, and semantic input value classes.
"""

from typing import Any

from apps.worker.alignment.models import ActionSignature
from apps.worker.exploration.candidate import CandidateAction
from apps.worker.exploration.transition import ExplorationTransition
from packages.domain.models import Action, ActionType


class ActionSignatureCalculator:
    """Computes deterministic, normalized ActionSignature from actions, candidates, or transitions."""

    @staticmethod
    def classify_input_value(
        value: str | None,
        tag: str = "",
        name_hint: str = "",
    ) -> str | None:
        """Deterministically map raw input values to normalized value classes."""
        if value is None:
            return None

        val_lower = value.lower()
        hint_lower = (name_hint or "").lower()

        if "@" in value or "email" in hint_lower or "email" in val_lower:
            return "EMAIL_VALUE"
        elif "search" in hint_lower or "query" in hint_lower or "q" == hint_lower:
            return "SEARCH_VALUE"
        elif value.isdigit() or "qty" in hint_lower or "num" in hint_lower or "quantity" in hint_lower:
            return "NUMBER_VALUE"
        elif "tel" in hint_lower or "phone" in hint_lower:
            return "TEL_VALUE"
        elif "date" in hint_lower or "-" in value and len(value) == 10:
            return "DATE_VALUE"

        return "TEXT_VALUE"

    @classmethod
    def from_candidate(cls, candidate: CandidateAction) -> ActionSignature:
        """Generate ActionSignature from an exploration CandidateAction."""
        metadata = candidate.metadata or {}
        tag = metadata.get("tag", "")
        acc_name = metadata.get("accessible_name")

        input_class = None
        if candidate.action_type in (ActionType.TYPE, ActionType.SELECT):
            input_class = cls.classify_input_value(
                value=candidate.value,
                tag=tag,
                name_hint=candidate.stable_element_id,
            )

        semantic_attrs: dict[str, str] = {}
        if tag:
            semantic_attrs["tag"] = tag

        return ActionSignature(
            action_type=candidate.action_type,
            stable_target_identity=candidate.stable_element_id,
            target_role=tag,
            accessible_name=acc_name,
            semantic_attributes=semantic_attrs,
            normalized_input_class=input_class,
            raw_target=candidate.target,
        )

    @classmethod
    def from_transition(cls, transition: ExplorationTransition) -> ActionSignature:
        """Generate ActionSignature from an ExplorationTransition."""
        target_id = transition.target_identity or transition.target
        input_class = None
        if transition.action_type in (ActionType.TYPE, ActionType.SELECT):
            input_class = cls.classify_input_value(
                value=transition.value,
                name_hint=target_id,
            )

        return ActionSignature(
            action_type=transition.action_type,
            stable_target_identity=target_id,
            normalized_input_class=input_class,
            raw_target=transition.target,
        )

    @classmethod
    def from_action(cls, action: Action, extra_meta: dict[str, Any] | None = None) -> ActionSignature:
        """Generate ActionSignature from a Phase 1 Action domain model."""
        meta = extra_meta or {}
        target_id = action.selector or meta.get("target", "")
        input_class = None
        if action.action_type in (ActionType.TYPE, ActionType.SELECT):
            input_class = cls.classify_input_value(
                value=action.value,
                name_hint=target_id,
            )

        return ActionSignature(
            action_type=action.action_type,
            stable_target_identity=target_id,
            target_role=meta.get("tag"),
            accessible_name=meta.get("accessible_name"),
            semantic_attributes=meta,
            normalized_input_class=input_class,
            raw_target=target_id,
        )
