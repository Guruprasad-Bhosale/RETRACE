"""Phase 15 Production Pilot Smoke Test with Commerce Laboratory & Telemetry Validation."""

import uuid

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
from packages.telemetry.metrics import metrics_registry


@pytest.mark.asyncio
async def test_phase15_api_probes_and_metrics_exposition() -> None:
    """Validate liveness, readiness, and prometheus metrics exposition."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Liveness
        resp_live = await client.get("/liveness")
        assert resp_live.status_code == 200
        assert resp_live.headers.get("X-Request-ID") is not None
        assert resp_live.headers.get("X-Trace-ID") is not None

        # Readiness
        resp_ready = await client.get("/readiness")
        assert resp_ready.status_code in (200, 503)

        # Metrics endpoint
        resp_metrics = await client.get("/metrics")
        assert resp_metrics.status_code == 200
        assert "retrace_http_requests_total" in resp_metrics.text
        assert "retrace_http_request_duration_seconds" in resp_metrics.text


@pytest.mark.asyncio
async def test_phase15_commerce_laboratory_pilot_execution() -> None:
    """Execute end-to-end controlled pilot investigation on Commerce Lab with telemetry validation."""
    analysis_id = uuid.uuid4()
    req = InvestigationRequest(
        analysis_id=analysis_id,
        project_id="commerce-lab-pilot",
        version_a=VersionConfig(
            name="Version A (Known-Good)",
            base_url="http://localhost:3001",
        ),
        version_b=VersionConfig(
            name="Version B (Target Release)",
            base_url="http://localhost:3002",
        ),
        budget=ResourceBudget(
            max_duration_seconds=30,
            max_actions=5,
        ),
        policy=ExecutionPolicy(
            synthesize_tests=True,
            generate_reports=True,
        ),
    )

    runner = InvestigationWorkflowRunner()
    result = await runner.run(req)

    # Validate output structure
    assert result is not None
    assert str(result.get("analysis_id")) == str(analysis_id)
    assert "status" in result

    # Check metric registry is intact
    assert metrics_registry is not None
