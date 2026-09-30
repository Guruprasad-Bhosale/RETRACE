"""Deterministic State Identity Projection Module.

Computes structural and behavioral state identity projections for exploration
equivalence, strictly separated from raw authoritative observation evidence.
"""

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse

from pydantic import BaseModel, ConfigDict

from packages.domain.models import Observation


class StateIdentity(BaseModel):
    """Deterministic projection representing application state for exploration equivalence."""

    model_config = ConfigDict(extra="forbid")

    state_id: str
    normalized_route: str
    inventory_signature: str
    a11y_signature: str
    ui_state_signature: str


class StateIdentityCalculator:
    """Projects Phase 3 Observations into deterministic StateIdentity tokens."""

    VOLATILE_QUERY_PARAMS = {
        "timestamp",
        "_t",
        "t",
        "cb",
        "nocache",
        "cachebuster",
        "v",
        "rand",
        "random",
        "_r",
        "session_id",
        "request_id",
    }

    @classmethod
    def normalize_route(cls, url: str) -> str:
        """Extract and normalize origin-relative path and stable query parameters."""
        if not url:
            return "/"

        try:
            parsed = urlparse(url)
            path = parsed.path or "/"
            # Normalize trailing slashes (except root)
            if len(path) > 1 and path.endswith("/"):
                path = path.rstrip("/")

            if not parsed.query:
                return path

            # Filter volatile parameters and sort remainder
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            stable_pairs = sorted(
                (k.lower(), v)
                for k, v in pairs
                if k.lower() not in cls.VOLATILE_QUERY_PARAMS
            )

            if stable_pairs:
                query_str = urlencode(stable_pairs)
                return f"{path}?{query_str}"
            return path
        except Exception:
            return url

    @classmethod
    def compute_inventory_signature(cls, observation: Observation) -> str:
        """Generate deterministic signature of actionable element inventory."""
        summary = observation.state.summary or {}
        inventory_breakdown = summary.get("inventory_breakdown", {})
        sorted_counts = sorted(inventory_breakdown.items(), key=lambda x: x[0])
        counts_str = ",".join(f"{k}:{v}" for k, v in sorted_counts)

        # Include interactive count
        return f"count={observation.state.interactive_elements_count};tags={counts_str}"

    @classmethod
    def compute_a11y_signature(cls, observation: Observation) -> str:
        """Extract accessibility structural signature."""
        return observation.state.a11y_tree_hash or "no_a11y"

    @classmethod
    def compute_ui_state_signature(cls, observation: Observation) -> str:
        """Extract selected stable UI state signals."""
        title = (observation.state.page_title or "").strip()
        # Clean ephemeral dynamic counts from titles like '(1) RETRACE Store'
        cleaned_title = re.sub(r"^\(\d+\)\s*", "", title)
        http_status = observation.state.http_status or 200
        return f"title={cleaned_title};status={http_status}"

    @classmethod
    def calculate(cls, observation: Observation) -> StateIdentity:
        """Calculate state identity projection from Phase 3 Observation."""
        route = cls.normalize_route(observation.state.url)
        inv_sig = cls.compute_inventory_signature(observation)
        a11y_sig = cls.compute_a11y_signature(observation)
        ui_sig = cls.compute_ui_state_signature(observation)

        projection_payload = f"route={route}|a11y={a11y_sig}|inv={inv_sig}|ui={ui_sig}"
        state_id = hashlib.sha256(projection_payload.encode("utf-8")).hexdigest()

        return StateIdentity(
            state_id=state_id,
            normalized_route=route,
            inventory_signature=inv_sig,
            a11y_signature=a11y_sig,
            ui_state_signature=ui_sig,
        )
