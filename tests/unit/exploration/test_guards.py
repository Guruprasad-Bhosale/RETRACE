"""Unit tests for URL and Action safety guards."""

from apps.worker.browser.inventory import ActionableElement
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.guards import ActionSafetyGuard, URLSafetyGuard
from packages.domain.models import ActionType


def test_url_safety_guard_allowed_and_disallowed():
    config = ExplorationConfig(
        seed_url="http://127.0.0.1:3001/index.html",
        allowed_domains=["127.0.0.1:3001", "cdn.example.com"],
    )
    guard = URLSafetyGuard(config)

    # Safe relative and same-origin URLs
    assert guard.is_safe_url("/cart.html", "http://127.0.0.1:3001/")[0] is True
    assert guard.is_safe_url("http://127.0.0.1:3001/checkout.html")[0] is True
    assert guard.is_safe_url("http://cdn.example.com/asset.js")[0] is True

    # Dangerous schemes
    assert guard.is_safe_url("javascript:alert(1)")[0] is False
    assert guard.is_safe_url("data:text/html,<h1>test</h1>")[0] is False
    assert guard.is_safe_url("file:///etc/passwd")[0] is False

    # Foreign external domain
    assert guard.is_safe_url("http://malicious-external-site.com")[0] is False


def test_action_safety_guard_distinguishes_navigation_from_destructive():
    config = ExplorationConfig(seed_url="http://localhost:3001", allow_destructive_actions=False)
    guard = ActionSafetyGuard(config)

    # 1. Navigational Checkout link/button -> ALLOWED
    checkout_btn = ActionableElement(
        tag="button",
        accessible_name="Proceed to Checkout",
        stable_identity="btn:checkout",
    )
    is_allowed, risk, _ = guard.evaluate_element_safety(checkout_btn, ActionType.CLICK)
    assert is_allowed is True
    assert risk == "safe"

    # 2. Actual Order Placement / Payment submission -> GUARDED / SKIPPED
    place_order_btn = ActionableElement(
        tag="button",
        accessible_name="Place Order",
        stable_identity="btn:place_order",
    )
    is_allowed, risk, _ = guard.evaluate_element_safety(place_order_btn, ActionType.CLICK)
    assert is_allowed is False
    assert risk == "destructive"

    # 3. Delete account button -> GUARDED / SKIPPED
    delete_btn = ActionableElement(
        tag="button",
        accessible_name="Delete Account Permanently",
        stable_identity="btn:delete_acc",
    )
    is_allowed, risk, _ = guard.evaluate_element_safety(delete_btn, ActionType.CLICK)
    assert is_allowed is False
    assert risk == "destructive"

    # 4. Password input field -> GUARDED
    pwd_input = ActionableElement(
        tag="input",
        element_type="password",
        stable_identity="inp:password",
    )
    is_allowed, risk, _ = guard.evaluate_element_safety(pwd_input, ActionType.TYPE)
    assert is_allowed is False
    assert risk == "destructive"
