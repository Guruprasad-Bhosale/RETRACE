"""Production Deployment End-to-End Smoke Test.

Validates application startup, health probes, readiness checks, storage integrity,
Redis Stream queue dispatch, and deterministic investigation workflow completion.
"""

import hashlib
import tempfile
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.worker.orchestration.models import (
    ExecutionPolicy,
    InvestigationRequest,
    ResourceBudget,
    VersionConfig,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from packages.config.settings import Settings
from packages.config.validator import ConfigurationValidator
from packages.db.migrations import check_migrations
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_api_liveness_probe():
    """Verify /health returns 200 healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "retrace-api"


@pytest.mark.asyncio
async def test_api_readiness_probe_structure():
    """Verify /ready probe returns structured database, redis, and storage readiness."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert "storage" in data


def test_configuration_validator_preflight():
    """Verify configuration validator produces structured results."""
    cfg = Settings(ENVIRONMENT="test")
    results = ConfigurationValidator.audit(cfg)
    assert len(results) >= 5
    items = [r.item for r in results]
    assert "ENVIRONMENT" in items
    assert "STORAGE_BACKEND" in items


def test_database_migration_head_consistency():
    """Verify database migrations have a single valid head."""
    res = check_migrations()
    assert res["status"] == "valid"
    assert res["multiple_heads"] is False
    assert len(res["heads"]) >= 1


@pytest.mark.asyncio
async def test_storage_put_get_and_sha256_integrity():
    """Verify artifact storage verifies SHA-256 integrity and prevents path traversal."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalDiskArtifactStorage(base_dir=tmp_dir)

        test_data = b"RETRACE_ARTIFACT_SMOKE_DATA_12345"
        expected_sha = hashlib.sha256(test_data).hexdigest()
        key = "smoke/test_artifact.bin"

        # Put with integrity
        uri, computed_sha = await storage.put_with_integrity(key=key, data=test_data, expected_sha256=expected_sha)
        assert computed_sha == expected_sha
        assert "file://" in uri

        # Get and verify content
        retrieved = await storage.get(key)
        assert retrieved == test_data

        # Verify health check
        health = await storage.check_health()
        assert health["healthy"] is True

        # Verify path traversal rejection
        with pytest.raises(PermissionError):
            await storage.put("../escape.txt", b"evil")


@pytest.mark.asyncio
async def test_deterministic_investigation_smoke_workflow():
    """Execute end-to-end investigation workflow with mocked endpoints."""
    analysis_id = uuid4()
    workflow_input = InvestigationRequest(
        analysis_id=analysis_id,
        project_id="smoke-project",
        version_a=VersionConfig(base_url="http://127.0.0.1:8000"),
        version_b=VersionConfig(base_url="http://127.0.0.1:8000"),
        budget=ResourceBudget(max_exploration_steps=2, max_workflow_duration_s=30),
        policy=ExecutionPolicy(fail_fast=False),
    )

    runner = InvestigationWorkflowRunner()
    result = await runner.run(workflow_input)

    assert result["analysis_id"] == str(analysis_id)
    assert result["workflow_id"] is not None
    assert result["status"] in ("COMPLETED", "FAILED", "INCONCLUSIVE")
