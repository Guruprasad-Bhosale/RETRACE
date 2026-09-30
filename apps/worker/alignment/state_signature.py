"""Deterministic State Signature Module.

Extracts normalized StateSignatures separating primary structural identity features
(route, state_id, inventory signature, a11y signature, ui state) from observational features
(HTTP status, console error counts, network failure counts, page title).
"""

import re

from apps.worker.alignment.models import StateObservationalFeatures, StateSignature
from apps.worker.exploration.state import ExplorationState
from apps.worker.exploration.state_identity import StateIdentityCalculator
from packages.domain.models import Observation


class StateSignatureCalculator:
    """Calculates deterministic StateSignature with explicit identity/observational separation."""

    @classmethod
    def clean_title(cls, title: str | None) -> str:
        """Clean ephemeral dynamic counters from page titles like '(1) RETRACE Store'."""
        if not title:
            return ""
        return re.sub(r"^\(\d+\)\s*", "", title.strip())

    @classmethod
    def from_exploration_state(
        cls,
        state: ExplorationState,
        observation: Observation | None = None,
    ) -> StateSignature:
        """Generate StateSignature from an ExplorationState, attaching Observation metrics when available."""
        normalized_route = StateIdentityCalculator.normalize_route(state.url)

        obs_features = StateObservationalFeatures()
        inv_sig = ""
        a11y_sig = ""
        ui_sig = ""

        if observation:
            identity = StateIdentityCalculator.calculate(observation)
            inv_sig = identity.inventory_signature
            a11y_sig = identity.a11y_signature
            ui_sig = identity.ui_state_signature

            obs_features = StateObservationalFeatures(
                http_status=observation.state.http_status,
                page_title=cls.clean_title(observation.state.page_title),
                console_errors_count=observation.state.console_errors_count,
                network_failures_count=observation.state.network_failures_count,
                interactive_elements_count=observation.state.interactive_elements_count,
            )
        else:
            # Fallback when observation entity is not directly attached
            ui_sig = f"title={normalized_route}"

        return StateSignature(
            state_id=state.state_id,
            normalized_route=normalized_route,
            inventory_signature=inv_sig,
            a11y_signature=a11y_sig,
            ui_state_signature=ui_sig,
            observational=obs_features,
        )

    @classmethod
    def from_observation(cls, observation: Observation) -> StateSignature:
        """Generate StateSignature directly from a Phase 3 Observation entity."""
        identity = StateIdentityCalculator.calculate(observation)

        obs_features = StateObservationalFeatures(
            http_status=observation.state.http_status,
            page_title=cls.clean_title(observation.state.page_title),
            console_errors_count=observation.state.console_errors_count,
            network_failures_count=observation.state.network_failures_count,
            interactive_elements_count=observation.state.interactive_elements_count,
        )

        return StateSignature(
            state_id=identity.state_id,
            normalized_route=identity.normalized_route,
            inventory_signature=identity.inventory_signature,
            a11y_signature=identity.a11y_signature,
            ui_state_signature=identity.ui_state_signature,
            observational=obs_features,
        )
