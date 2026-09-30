"""Safety Guards and Destructive Action Policy Module."""

from urllib.parse import urljoin, urlparse

from apps.worker.browser.inventory import ActionableElement
from apps.worker.exploration.config import ExplorationConfig
from packages.domain.models import ActionType


class URLSafetyGuard:
    """Validates URLs against allowed origins, schemes, and domain boundaries."""

    def __init__(self, config: ExplorationConfig) -> None:
        self.config = config
        self.allowed_domains = self.config.get_effective_allowed_domains()
        self.allowed_schemes = {s.lower() for s in self.config.allowed_url_schemes}

    def resolve_url(self, target: str, current_base_url: str) -> str:
        """Resolve relative URL against base URL."""
        if not target:
            return current_base_url
        return urljoin(current_base_url, target)

    def is_safe_url(self, target: str, current_base_url: str = "") -> tuple[bool, str]:
        """Check if target URL is within allowed domain and scheme boundaries."""
        if not target:
            return False, "Empty URL"

        resolved = self.resolve_url(target, current_base_url)
        try:
            parsed = urlparse(resolved)
        except Exception as e:
            return False, f"Malformed URL: {e}"

        # 1. Scheme verification
        scheme = parsed.scheme.lower()
        if not scheme:
            return False, "Missing URL scheme"
        if scheme not in self.allowed_schemes:
            return False, f"Disallowed URL scheme: {scheme}"

        # 2. Domain verification
        netloc = parsed.netloc.lower()
        if not netloc:
            return False, "Missing network location / host"

        # Match exact domain or port-included domain
        host_only = netloc.split(":")[0]
        if not any(
            netloc == d or host_only == d or host_only.endswith(f".{d}")
            for d in self.allowed_domains
        ):
            return False, f"Domain {netloc} not in allowed domains list"

        return True, "Safe"


class ActionSafetyGuard:
    """Evaluates actionable element risk and prevents hazardous state mutations."""

    # Keywords for hazardous mutations (actual destructive operations or payment submissions)
    HAZARDOUS_KEYWORDS = {
        "place order",
        "submit order",
        "complete order",
        "confirm order",
        "pay now",
        "submit payment",
        "complete purchase",
        "buy now",
        "delete account",
        "delete item",
        "delete all",
        "wipe data",
        "drop database",
        "sign out",
        "log out",
        "logout",
        "terminate account",
        "cancel subscription",
    }

    # Safe navigational terms even if they resemble transaction flow
    SAFE_NAVIGATIONAL_TERMS = {
        "checkout",
        "proceed to checkout",
        "go to checkout",
        "view cart",
        "cart",
        "add to cart",
        "apply",
        "apply coupon",
        "search",
        "filter",
        "next",
        "previous",
        "details",
        "view",
    }

    def __init__(self, config: ExplorationConfig) -> None:
        self.config = config

    def evaluate_element_safety(
        self,
        element: ActionableElement,
        action_type: ActionType,
    ) -> tuple[bool, str, str]:
        """Evaluate if an interactive element is safe to interact with.

        Returns: (is_allowed, risk_level, reason)
        risk_level is one of "safe", "caution", or "destructive".
        """
        if self.config.allow_destructive_actions:
            return True, "safe", "Destructive actions explicitly enabled"

        # 1. Password field safety
        if element.tag == "input" and (element.element_type or "").lower() == "password":
            return False, "destructive", "Password inputs are guarded by default"

        # 2. Textual context inspection
        combined_text = " ".join(
            filter(
                None,
                [
                    element.accessible_name,
                    element.associated_label,
                    element.test_id,
                    element.dom_id,
                    element.name_attr,
                    element.placeholder,
                    element.attributes.get("value"),
                    element.attributes.get("title"),
                    element.attributes.get("aria-label"),
                ],
            )
        ).lower()

        # Check explicit safe overrides (e.g. "proceed to checkout" button)
        if any(safe_term in combined_text for safe_term in self.SAFE_NAVIGATIONAL_TERMS):
            # If it's a navigational checkout button/link, it's safe
            if not any(mut_term in combined_text for mut_term in ("place order", "pay now", "buy now")):
                return True, "safe", "Safe navigational element"

        # Check hazardous keywords
        for keyword in self.HAZARDOUS_KEYWORDS:
            if keyword in combined_text:
                return (
                    False,
                    "destructive",
                    f"Action matches hazardous keyword: '{keyword}'",
                )

        # Form submissions for destructive buttons
        if element.tag == "button" or (element.tag == "input" and element.element_type == "submit"):
            if any(term in combined_text for term in ("delete", "remove", "wipe", "destroy", "cancel")):
                return False, "destructive", "Destructive form submission button"

        return True, "safe", "Safe element"
