"""Controlled Production Failure Injection and Resilience Test Suite."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.worker.main import AnalysisWorker
from packages.auth.models import Action, Principal, Role
from packages.auth.rbac import authorize
from packages.config.settings import Settings
from packages.redis_client.queue import JobMessage, RedisStreamWorkerQueue


@pytest.mark.asyncio
async def test_failure_injection_redis_unavailable() -> None:
    """When Redis is unavailable, readiness probe fails with 503 and API does not corrupt state."""
    with patch(
        "apps.api.routers.health.check_redis_health",
        new=AsyncMock(return_value={"healthy": False, "status": "down", "error": "Connection refused"}),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Liveness remains healthy
            resp_live = await client.get("/liveness")
            assert resp_live.status_code == 200

            # Readiness returns 503 Service Unavailable
            resp_ready = await client.get("/ready")
            assert resp_ready.status_code == 503
            data = resp_ready.json()
            assert data["status"] == "degraded"
            assert data["redis"]["healthy"] is False


@pytest.mark.asyncio
async def test_failure_injection_database_unavailable() -> None:
    """When PostgreSQL is down, readiness returns 503 while liveness remains 200."""
    with patch(
        "apps.api.routers.health.check_database_health",
        new=AsyncMock(return_value={"healthy": False, "status": "down", "error": "FATAL: connection limit"}),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_live = await client.get("/health")
            assert resp_live.status_code == 200

            resp_ready = await client.get("/readiness")
            assert resp_ready.status_code == 503
            assert resp_ready.json()["database"]["healthy"] is False


@pytest.mark.asyncio
async def test_failure_injection_worker_crash_and_recovery() -> None:
    """Simulate worker crash leaving job pending, recovered by another worker via XAUTOCLAIM."""
    mock_redis = AsyncMock()
    # Mock XAUTOCLAIM returning a pending job
    test_msg_id = "1720000000000-0"
    mock_redis.xautoclaim.return_value = (
        "0-0",
        [
            (
                test_msg_id,
                {
                    "job_id": "job-recovered-123",
                    "job_type": "investigation",
                    "payload": '{"analysis_id": "00000000-0000-0000-0000-000000000099", "version_a": {"base_url": "http://a"}, "version_b": {"base_url": "http://b"}}',
                    "request_id": "req-999",
                    "trace_id": "trace-999",
                },
            )
        ],
        [],
    )

    queue = RedisStreamWorkerQueue(
        settings=Settings(ENVIRONMENT="test"),
        consumer_name="worker-replica-2",
        redis_client=mock_redis,
    )
    recovered = await queue.recover_pending_jobs(min_idle_time_ms=1000)

    assert len(recovered) == 1
    assert recovered[0].job_id == "job-recovered-123"
    assert recovered[0].request_id == "req-999"
    assert recovered[0].trace_id == "trace-999"


@pytest.mark.asyncio
async def test_failure_injection_browser_failure_handling() -> None:
    """Browser crash during analysis logs failure without raising unhandled exception."""
    worker = AnalysisWorker()
    worker.worker_id = "test-worker-browser-fail"
    worker.queue = AsyncMock()

    # Create job message that triggers a failing runner
    job = JobMessage(
        message_id="1-0",
        stream_key="retrace:analysis:jobs",
        job_id="fail-job-1",
        job_type="investigation",
        payload={
            "analysis_id": str(uuid.uuid4()),
            "version_a": {"base_url": "http://localhost:9999"},
            "version_b": {"base_url": "http://localhost:9999"},
        },
    )

    with patch("apps.worker.main.InvestigationWorkflowRunner") as mock_runner_cls:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run = AsyncMock(side_effect=RuntimeError("Browser closed unexpectedly (SIGKILL)"))

        # Process job should catch the exception and log failure
        await worker.process_job(job)

        # Ensure failed job did not call acknowledge_job
        worker.queue.acknowledge_job.assert_not_called()


def test_failure_injection_invalid_authorization() -> None:
    """Invalid caller credentials reject without resource leakage."""
    ws_1 = uuid.uuid4()
    ws_2 = uuid.uuid4()
    viewer = Principal(id=uuid.uuid4(), workspace_id=ws_1, role=Role.VIEWER)

    # Viewer attempting write operations
    assert authorize(viewer, Action.PROJECT_DELETE, ws_1) is False
    assert authorize(viewer, Action.ANALYSIS_EXECUTE, ws_1) is False

    # Viewer attempting cross-workspace read
    assert authorize(viewer, Action.INVESTIGATION_VIEW, ws_2) is False
