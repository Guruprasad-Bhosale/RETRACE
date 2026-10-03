"""Forensic Sanitizer & Prompt-Injection Resistance Module.

Enforces zero-trust boundaries for untrusted browser/DOM/network payloads and
validates that all evidence references correspond strictly to verified items in the investigation catalog.
"""

import re

from packages.forensics.models import ForensicEvidenceItem


class ForensicSecurityError(Exception):
    """Base exception for forensic security and integrity violations."""


class InvalidEvidenceReferenceError(ForensicSecurityError):
    """Raised when an intelligence output references an unknown or non-existent evidence ID."""


class PromptInjectionAttemptDetected(ForensicSecurityError):
    """Raised or flagged when an adversarial prompt injection pattern is detected in observed data."""


# Known adversarial prompt injection triggers to detect and neutralize
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+(prompt\s+override|prompt|override)\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),

    re.compile(r"the\s+root\s+cause\s+is\s+(definitely|file\s+\w+)", re.IGNORECASE),
    re.compile(r"do\s+not\s+report\s+this\s+bug", re.IGNORECASE),
    re.compile(r"bypass\s+security\s+audit", re.IGNORECASE),
    re.compile(r"assistant\s*:", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(telemetry|dom\s+diffs|evidence)", re.IGNORECASE),
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
]


class ForensicSanitizer:
    """Sanitizes untrusted web observations and verifies evidence reference integrity."""

    @staticmethod
    def sanitize_string(text: str, max_length: int = 4096) -> str:
        """Sanitize text and replace adversarial injection attempts with neutralization token."""
        sanitized, _ = ForensicSanitizer.sanitize_untrusted_text(text, max_length=max_length)
        return sanitized

    @staticmethod
    def sanitize_untrusted_text(text: str, max_length: int = 4096) -> tuple[str, bool]:
        """Sanitize untrusted text from DOM/network/console and flag injection attempts.

        Returns:
            tuple of (sanitized_text, injection_detected_bool)
        """
        if not text:
            return "", False

        # Bound length to prevent resource exhaustion attacks
        truncated = text[:max_length]
        injection_found = False

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(truncated):
                injection_found = True
                # Neutralize by escaping and tagging as untrusted observational string
                truncated = pattern.sub(r"[UNTRUSTED_CONTENT_NEUTRALIZED]", truncated)

        return truncated.strip(), injection_found



    @staticmethod
    def validate_evidence_references(
        referenced_ids: list[str] | set[str],
        valid_evidence_catalog: dict[str, ForensicEvidenceItem] | set[str] | list[str],
    ) -> None:
        """Verify all referenced evidence IDs exist in the authoritative catalog (Fail-Closed).

        Raises:
            InvalidEvidenceReferenceError: if any ID is missing or hallucinated.
        """
        if isinstance(valid_evidence_catalog, dict):
            valid_set = set(valid_evidence_catalog.keys())
        elif isinstance(valid_evidence_catalog, list):
            valid_set = set(valid_evidence_catalog)
        else:
            valid_set = valid_evidence_catalog

        for ref_id in referenced_ids:
            if not ref_id:
                continue
            if ref_id not in valid_set:
                raise InvalidEvidenceReferenceError(
                    f"Forensic validation failed: Evidence ID '{ref_id}' does not exist in the "
                    f"investigation evidence catalog (valid IDs count: {len(valid_set)}). Output rejected."
                )

    @staticmethod
    def sanitize_evidence_item(item: ForensicEvidenceItem) -> ForensicEvidenceItem:
        """Ensure evidence item is marked untrusted if originating from external observations."""
        clean_obs, injection_flag = ForensicSanitizer.sanitize_untrusted_text(item.observation)
        metadata = dict(item.metadata)
        if injection_flag:
            metadata["prompt_injection_attempt_detected"] = True

        return item.model_copy(
            update={
                "observation": clean_obs,
                "metadata": metadata,
                "is_untrusted_input": True,
            }
        )
