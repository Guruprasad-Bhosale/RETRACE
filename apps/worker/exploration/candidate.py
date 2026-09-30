"""Deterministic Candidate Action Generation Module."""

import hashlib
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.browser.inventory import ActionableElement, ElementInventory
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.guards import ActionSafetyGuard, URLSafetyGuard
from packages.domain.models import ActionType


class CandidateAction(BaseModel):
    """Deterministic candidate action generated from observed application state."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    action_type: ActionType
    target: str
    target_strategy: str = "auto"
    value: str | None = None
    stable_element_id: str
    source_state_id: str
    source_observation_id: UUID
    document_order: int = Field(ge=0, description="0-indexed position in document inventory")
    risk_level: str = "safe"
    is_navigational: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_ordering_key(self) -> tuple[int, str, str, str, int]:
        """Strict deterministic tie-breaking ordering key."""
        risk_prio = 0 if self.risk_level == "safe" else (1 if self.risk_level == "caution" else 2)
        tag = self.metadata.get("tag", "")
        return (
            risk_prio,
            self.action_type.value,
            tag,
            self.stable_element_id,
            self.document_order,
        )


class CandidateGenerator:
    """Generates and sorts candidate actions deterministically from Phase 3 element inventories."""

    def __init__(
        self,
        config: ExplorationConfig,
        safety_guard: ActionSafetyGuard | None = None,
        url_guard: URLSafetyGuard | None = None,
    ) -> None:
        self.config = config
        self.safety_guard = safety_guard or ActionSafetyGuard(config)
        self.url_guard = url_guard or URLSafetyGuard(config)

    def _resolve_synthetic_value(self, element: ActionableElement) -> str:
        """Select safe deterministic synthetic input value based on element type/name."""
        el_type = (element.element_type or "text").lower()
        name_hint = (element.name_attr or element.dom_id or "").lower()

        if "email" in el_type or "email" in name_hint:
            return self.config.synthetic_inputs.get("email", "retrace@example.invalid")
        elif "search" in el_type or "search" in name_hint or "query" in name_hint or "q" == name_hint:
            return self.config.synthetic_inputs.get("search", "test")
        elif "num" in el_type or "qty" in name_hint or "quantity" in name_hint:
            return self.config.synthetic_inputs.get("number", "1")
        elif "tel" in el_type or "phone" in name_hint:
            return self.config.synthetic_inputs.get("tel", "555-0199")
        elif "date" in el_type:
            return self.config.synthetic_inputs.get("date", "2026-01-01")

        return self.config.synthetic_inputs.get("text", "retrace-test")

    def generate_candidates(
        self,
        inventory: ElementInventory,
        source_state_id: str,
        source_observation_id: UUID,
        current_url: str = "",
    ) -> list[CandidateAction]:
        """Extract and deterministically rank candidate actions from actionable element inventory."""
        candidates: list[CandidateAction] = []

        for index, element in enumerate(inventory.elements):
            if not element.is_visible or not element.is_enabled:
                continue

            tag = element.tag.lower()
            el_type = (element.element_type or "").lower()

            action_type: ActionType
            is_nav = False
            value: str | None = None

            # 1. Determine action type
            if tag == "a" or element.role == "link":
                action_type = ActionType.CLICK
                is_nav = True
                # Verify URL safety for links
                if element.href:
                    is_safe, _ = self.url_guard.is_safe_url(element.href, current_url)
                    if not is_safe:
                        continue

            elif tag == "button" or element.role == "button":
                action_type = ActionType.CLICK
                # Buttons navigating to other views (like cart/checkout)
                btn_text = (element.accessible_name or "").lower()
                if "cart" in btn_text or "checkout" in btn_text or "view" in btn_text:
                    is_nav = True

            elif tag in ("input", "textarea"):
                if el_type in ("checkbox", "radio", "submit", "button"):
                    action_type = ActionType.CLICK
                else:
                    action_type = ActionType.TYPE
                    value = self._resolve_synthetic_value(element)

            elif tag == "select":
                action_type = ActionType.SELECT
                value = element.value or "1"

            else:
                action_type = ActionType.CLICK

            # 2. Safety evaluation
            is_allowed, risk_level, reason = self.safety_guard.evaluate_element_safety(
                element=element,
                action_type=action_type,
            )

            if not is_allowed and not self.config.allow_destructive_actions:
                continue

            # 3. Construct target identifier
            target = element.stable_identity
            target_strategy = "auto"
            if element.test_id:
                target = f"testid:{element.test_id}"
                target_strategy = "testid"
            elif element.dom_id:
                target = f"css:#{element.dom_id}"
                target_strategy = "css"
            elif element.selector_candidates:
                target = element.selector_candidates[0]

            # 4. Generate candidate ID
            cid_raw = (
                f"{source_state_id}|{action_type.value}|{element.stable_identity}|"
                f"{value or ''}|{index}"
            )
            candidate_id = hashlib.sha256(cid_raw.encode("utf-8")).hexdigest()[:16]

            candidates.append(
                CandidateAction(
                    candidate_id=candidate_id,
                    action_type=action_type,
                    target=target,
                    target_strategy=target_strategy,
                    value=value,
                    stable_element_id=element.stable_identity,
                    source_state_id=source_state_id,
                    source_observation_id=source_observation_id,
                    document_order=index,
                    risk_level=risk_level,
                    is_navigational=is_nav,
                    metadata={
                        "tag": tag,
                        "accessible_name": element.accessible_name,
                        "safety_reason": reason,
                        "element_index": index,
                    },
                )
            )

        # 5. Sort deterministically using explicit tie-breaking key
        candidates.sort(key=lambda c: c.compute_ordering_key())

        # Cap max actions per state according to config
        return candidates[: self.config.max_actions_per_state]
