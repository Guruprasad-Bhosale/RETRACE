"""Deterministic Normalization Utilities for Semantic Difference Analysis.

Ensures comparison inputs are normalized without representation noise while preserving
full semantic intent and strictly preventing secret leakage.
"""

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

from apps.worker.diff.config import DiffConfig


class DiffNormalizer:
    """Deterministic normalizer across routes, text, attributes, and metrics."""

    @staticmethod
    def normalize_route(route: str, config: DiffConfig | None = None) -> str:
        """Normalize URL/route string by removing protocol/host/port and applying matching policies."""
        if not route:
            return "/"

        parsed = urlparse(route.strip())
        path = parsed.path or "/"

        if config and config.route_matching_policy == "strict":
            if parsed.query:
                # Sort query parameters deterministically
                q_params = sorted(parse_qsl(parsed.query))
                return f"{path}?{urlencode(q_params)}"
            return path

        if config and config.route_matching_policy == "allow_aliases":
            canonical = path
            for root, aliases in config.route_aliases.items():
                if path == root or path in aliases:
                    canonical = root
                    break
            return canonical

        # Default policy: strip_query
        return path

    @staticmethod
    def normalize_text(text: str | None) -> str:
        """Conservatively normalize text content by standardizing whitespace and line endings."""
        if text is None:
            return ""
        # Normalize line endings
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        # Strip leading/trailing whitespace
        return cleaned.strip()

    @staticmethod
    def normalize_attribute_value(name: str, value: Any) -> str:
        """Normalize DOM/A11y attribute values deterministically."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        str_val = str(value).strip()
        # Case fold common boolean or enumerated attributes
        if name.lower() in ("disabled", "checked", "required", "aria-disabled", "aria-checked", "aria-required", "aria-expanded", "aria-hidden"):
            return str_val.lower()
        return str_val

    @staticmethod
    def normalize_timing(duration_ms: float | None, precision: int = 2) -> float:
        """Round duration to fixed decimal precision for deterministic comparisons."""
        if duration_ms is None:
            return 0.0
        return round(float(duration_ms), precision)

    @staticmethod
    def sanitize_diff_payload(payload: dict[str, Any]) -> dict[str, Any]:
        """Verify and strip any sensitive key-value pairs before embedding into difference payloads."""
        sensitive_patterns = {"authorization", "cookie", "set-cookie", "token", "password", "secret", "api_key", "apikey"}
        sanitized: dict[str, Any] = {}

        for k, v in payload.items():
            if any(p in k.lower() for p in sensitive_patterns):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = DiffNormalizer.sanitize_diff_payload(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    DiffNormalizer.sanitize_diff_payload(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                sanitized[k] = v

        return sanitized
