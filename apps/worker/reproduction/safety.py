"""Safety Guards for Deterministic Replay Execution."""

import re
from urllib.parse import urlparse

from apps.worker.reproduction.config import SafetyPolicy
from apps.worker.reproduction.errors import SafetyViolationError
from apps.worker.reproduction.models import ReproductionPath, ReproductionStep


class ReproductionSafetyGuard:
    """Enforces safety boundaries, domain restrictions, and destructive interaction prevention."""

    def __init__(self, policy: SafetyPolicy) -> None:
        self.policy = policy
        self._blocked_patterns = [
            (kw, re.compile(re.escape(kw), re.IGNORECASE)) for kw in self.policy.blocked_keywords
        ]

    def is_url_allowed(self, url: str) -> bool:
        """Check whether target URL is permitted under domain boundaries."""
        if not url:
            return False
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not self.policy.allowed_domains:
            return True
        hostname = (parsed.hostname or "").lower()
        return any(
            hostname == domain.lower() or hostname.endswith("." + domain.lower())
            for domain in self.policy.allowed_domains
        )

    def is_action_safe(self, step: ReproductionStep) -> tuple[bool, str | None]:
        """Verify that an individual step does not trigger a destructive or hazardous operation."""
        if not self.policy.block_destructive_actions:
            return True, None

        # Check target strings and text values
        candidates = [
            step.stable_target_identity or "",
            step.accessible_name or "",
            step.raw_target or "",
            step.value or "",
        ]
        text_to_check = " ".join(candidates)

        for kw, pattern in self._blocked_patterns:
            if pattern.search(text_to_check):
                return False, f"Step {step.step_index} matches blocked destructive pattern '{kw}'"

        return True, None

    def validate_path_safety(self, path: ReproductionPath) -> None:
        """Validate entire reproduction path before browser execution.

        Raises:
            SafetyViolationError: If seed URL or any step violates safety policies.
        """
        if not self.is_url_allowed(path.seed_url):
            raise SafetyViolationError(
                f"Seed URL '{path.seed_url}' is not in allowed reproduction domains."
            )

        for step in path.steps:
            safe, reason = self.is_action_safe(step)
            if not safe:
                raise SafetyViolationError(reason or f"Unsafe step detected at index {step.step_index}")
