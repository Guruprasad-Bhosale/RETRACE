"""Unit tests for Normalization Utilities in Semantic Diff Engine."""

from apps.worker.diff.config import DiffConfig
from apps.worker.diff.normalization import DiffNormalizer


def test_route_normalization_host_and_port():
    assert DiffNormalizer.normalize_route("http://localhost:3001/checkout") == "/checkout"
    assert DiffNormalizer.normalize_route("http://127.0.0.1:8080/cart/") == "/cart/"
    assert DiffNormalizer.normalize_route("https://example.com/api/v1/items?page=1") == "/api/v1/items"


def test_route_normalization_policies():
    strict_cfg = DiffConfig(route_matching_policy="strict")
    assert DiffNormalizer.normalize_route("http://localhost/cart?b=2&a=1", strict_cfg) == "/cart?a=1&b=2"

    alias_cfg = DiffConfig(
        route_matching_policy="allow_aliases",
        route_aliases={"/cart": ["/basket", "/bag"]},
    )
    assert DiffNormalizer.normalize_route("http://localhost/basket", alias_cfg) == "/cart"
    assert DiffNormalizer.normalize_route("http://localhost/bag", alias_cfg) == "/cart"
    assert DiffNormalizer.normalize_route("http://localhost/other", alias_cfg) == "/other"


def test_text_normalization():
    assert DiffNormalizer.normalize_text("  hello \r\n world  ") == "hello \n world"
    assert DiffNormalizer.normalize_text(None) == ""


def test_attribute_normalization():
    assert DiffNormalizer.normalize_attribute_value("disabled", True) == "true"
    assert DiffNormalizer.normalize_attribute_value("disabled", "Disabled") == "disabled"
    assert DiffNormalizer.normalize_attribute_value("placeholder", " Enter Name ") == "Enter Name"


def test_timing_normalization():
    assert DiffNormalizer.normalize_timing(124.5678) == 124.57
    assert DiffNormalizer.normalize_timing(None) == 0.0


def test_secret_sanitization():
    payload = {
        "url": "http://example.com/login",
        "Authorization": "Bearer secret-token-123",
        "nested": {
            "password": "super-secret-password",
            "safe_field": "public_data",
        },
        "cookies": ["session=xyz"],
    }
    sanitized = DiffNormalizer.sanitize_diff_payload(payload)
    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "public_data"
    assert sanitized["cookies"] == "[REDACTED]"
