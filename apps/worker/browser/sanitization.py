"""Centralized Data Sanitization and Secret Redaction Module.

Ensures sensitive credentials, authorization headers, cookies, tokens, and
binary payloads are never persisted into evidence or observation logs.
"""

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from apps.worker.browser.config import NetworkCapturePolicy

REDACTED_VALUE = "[REDACTED]"
TRUNCATED_MARKER = "\n...[TRUNCATED_DUE_TO_SIZE_LIMIT]"
BINARY_PLACEHOLDER = "[BINARY_PAYLOAD_OMITTED]"


class DataSanitizer:
    """Sanitizes URLs, headers, bodies, and structured dictionaries."""

    def __init__(self, policy: NetworkCapturePolicy | None = None) -> None:
        self.policy = policy or NetworkCapturePolicy()
        self._redact_headers = {h.lower() for h in self.policy.redact_headers}
        self._redact_params = {p.lower() for p in self.policy.redact_query_params}
        self._redact_body_fields = {f.lower() for f in self.policy.redact_body_fields}

    def sanitize_url(self, url: str) -> str:
        """Redact sensitive query parameters from a URL."""
        if not url:
            return url

        try:
            parsed = urlparse(url)
            if not parsed.query:
                return url

            query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            sanitized_pairs = []
            for key, val in query_pairs:
                if key.lower() in self._redact_params or any(
                    secret_term in key.lower() for secret_term in ("token", "key", "secret", "auth", "pwd")
                ):
                    sanitized_pairs.append((key, REDACTED_VALUE))
                else:
                    sanitized_pairs.append((key, val))

            new_query = urlencode(sanitized_pairs)
            return urlunparse(parsed._replace(query=new_query))
        except Exception:
            return url

    def sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Redact sensitive HTTP headers."""
        sanitized = {}
        for key, value in headers.items():
            k_lower = key.lower()
            if k_lower in self._redact_headers or any(
                secret_term in k_lower for secret_term in ("auth", "cookie", "token", "key", "secret")
            ):
                sanitized[key] = REDACTED_VALUE
            else:
                sanitized[key] = value
        return sanitized

    def sanitize_structured_data(self, data: Any) -> Any:
        """Recursively redact sensitive keys in nested dictionaries/lists."""
        if isinstance(data, dict):
            sanitized_dict = {}
            for k, v in data.items():
                if isinstance(k, str) and (
                    k.lower() in self._redact_body_fields
                    or any(st in k.lower() for st in ("password", "secret", "token", "card", "cvv"))
                ):
                    sanitized_dict[k] = REDACTED_VALUE
                else:
                    sanitized_dict[k] = self.sanitize_structured_data(v)
            return sanitized_dict
        elif isinstance(data, list):
            return [self.sanitize_structured_data(item) for item in data]
        return data

    def sanitize_body(
        self,
        raw_body: bytes | str | None,
        content_type: str | None = None,
    ) -> str | None:
        """Process, validate, redact, and bound HTTP payload bodies according to policy."""
        if not self.policy.capture_bodies or raw_body is None:
            return None

        # Content type verification
        c_type = (content_type or "").lower().split(";")[0].strip()
        if c_type and not any(allowed in c_type for allowed in self.policy.allowed_content_types):
            return BINARY_PLACEHOLDER

        # Convert bytes to string safely
        text: str
        if isinstance(raw_body, bytes):
            # Check for non-text / binary indicators
            try:
                text = raw_body.decode("utf-8")
            except UnicodeDecodeError:
                return BINARY_PLACEHOLDER
        else:
            text = str(raw_body)

        # JSON parsing and sensitive field redaction
        if "json" in c_type or text.startswith(("{", "[")):
            try:
                parsed_json = json.loads(text)
                sanitized_json = self.sanitize_structured_data(parsed_json)
                text = json.dumps(sanitized_json)
            except Exception:
                pass

        # Size bounding and deterministic truncation
        max_bytes = self.policy.max_body_bytes
        encoded_bytes = text.encode("utf-8")
        if len(encoded_bytes) > max_bytes:
            truncated = encoded_bytes[:max_bytes].decode("utf-8", errors="ignore")
            return truncated + TRUNCATED_MARKER

        return text
