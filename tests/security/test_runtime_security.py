"""Runtime Security, SSRF Prevention, and Oracle Isolation Tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.worker.reproduction.config import SafetyPolicy
from apps.worker.reproduction.safety import ReproductionSafetyGuard
from packages.security.audit import SecurityAuditor


def test_reproduction_safety_guard_blocks_cloud_metadata_and_ssrf():
    """Verify ReproductionSafetyGuard strictly blocks AWS metadata service (169.254.169.254) and unauthorized external domains."""
    policy = SafetyPolicy(allowed_domains=["localhost", "127.0.0.1", "example.com"])
    guard = ReproductionSafetyGuard(policy=policy)

    # Block AWS metadata endpoint
    assert guard.is_url_allowed("http://169.254.169.254/latest/meta-data/") is False
    assert guard.is_url_allowed("http://169.254.169.254/latest/api/token") is False

    # Block unauthorized external domains
    assert guard.is_url_allowed("https://malicious-external-site.evil.com") is False

    # Allow configured test domains
    assert guard.is_url_allowed("http://localhost:3000/cart") is True
    assert guard.is_url_allowed("http://127.0.0.1:3001/checkout") is True


def test_security_auditor_reports_zero_violations():
    """Verify static security auditor finds zero credential leaks or oracle violations."""
    auditor = SecurityAuditor()
    findings = auditor.scan_all()
    assert len(findings) == 0, f"Security auditor found {len(findings)} violations: {findings}"


@pytest.mark.asyncio
async def test_api_error_responses_sanitize_stack_traces_in_production(async_client: AsyncClient):
    """Verify API error responses sanitize internal exceptions and do not leak tracebacks."""
    # Send malformed PATCH status update with invalid payload
    bad_id = str(uuid4())
    res = await async_client.patch(
        f"/api/v1/analyses/{bad_id}/status",
        json={"current_version": "not_an_integer", "status": "running"},
    )
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    # Ensure raw Python stack trace is not exposed
    assert "Traceback (most recent call last)" not in res.text
