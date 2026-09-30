"""Unit tests for centralized data sanitization and redaction."""

from apps.worker.browser.config import NetworkCapturePolicy
from apps.worker.browser.sanitization import (
    BINARY_PLACEHOLDER,
    REDACTED_VALUE,
    TRUNCATED_MARKER,
    DataSanitizer,
)


def test_sanitize_url_redacts_tokens_and_secrets():
    sanitizer = DataSanitizer()
    url = "https://example.com/api/v1?token=secret123&user=john&apiKey=xyz987&normal=1"
    clean = sanitizer.sanitize_url(url)
    assert f"token={REDACTED_VALUE}" in clean or "token=%5BREDACTED%5D" in clean
    assert f"apiKey={REDACTED_VALUE}" in clean or "apiKey=%5BREDACTED%5D" in clean
    assert "user=john" in clean
    assert "normal=1" in clean


def test_sanitize_headers_redacts_auth_and_cookies():
    sanitizer = DataSanitizer()
    headers = {
        "Authorization": "Bearer super-secret-token",
        "Cookie": "session_id=abc1234; user=john",
        "Set-Cookie": "auth=secret;",
        "Content-Type": "application/json",
        "X-Custom-Header": "regular_value",
    }
    clean = sanitizer.sanitize_headers(headers)
    assert clean["Authorization"] == REDACTED_VALUE
    assert clean["Cookie"] == REDACTED_VALUE
    assert clean["Set-Cookie"] == REDACTED_VALUE
    assert clean["Content-Type"] == "application/json"
    assert clean["X-Custom-Header"] == "regular_value"


def test_sanitize_body_disabled_by_default():
    policy = NetworkCapturePolicy(capture_bodies=False)
    sanitizer = DataSanitizer(policy)
    assert sanitizer.sanitize_body(b'{"key": "val"}', "application/json") is None


def test_sanitize_body_json_redaction():
    policy = NetworkCapturePolicy(capture_bodies=True)
    sanitizer = DataSanitizer(policy)
    body = '{"username": "admin", "password": "supersecretpassword", "token": "tok123"}'
    clean = sanitizer.sanitize_body(body, "application/json")
    assert clean is not None
    assert '"admin"' in clean
    assert '"supersecretpassword"' not in clean
    assert f'"{REDACTED_VALUE}"' in clean


def test_sanitize_body_truncation():
    policy = NetworkCapturePolicy(capture_bodies=True, max_body_bytes=50)
    sanitizer = DataSanitizer(policy)
    large_text = "A" * 200
    clean = sanitizer.sanitize_body(large_text, "text/plain")
    assert clean is not None
    assert len(clean) < 150
    assert TRUNCATED_MARKER in clean


def test_sanitize_body_binary_protection():
    policy = NetworkCapturePolicy(capture_bodies=True)
    sanitizer = DataSanitizer(policy)
    clean = sanitizer.sanitize_body(b"\x00\x01\x02\xff\xfe", "application/octet-stream")
    assert clean == BINARY_PLACEHOLDER
