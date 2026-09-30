"""Integration tests for FastAPI workflow management endpoints."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app


@pytest.mark.asyncio
async def test_workflow_api_lifecycle():
    """Verify start, status query, cancel, and resume endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        analysis_id = str(uuid4())
        start_payload = {
            "project_id": "api-test-project",
            "analysis_id": analysis_id,
            "version_a": {"base_url": "http://127.0.0.1:8001"},
            "version_b": {"base_url": "http://127.0.0.1:8002"},
        }

        # 1. Start workflow in background
        resp_start = await client.post("/api/v1/investigations/start", json=start_payload)
        assert resp_start.status_code == 202
        start_data = resp_start.json()
        workflow_id = start_data["workflow_id"]
        assert workflow_id is not None
        assert start_data["status"] == "PENDING"

        # 2. Query status
        resp_status = await client.get(f"/api/v1/investigations/workflow/{workflow_id}/status")
        assert resp_status.status_code == 200
        status_data = resp_status.json()
        assert status_data["workflow_id"] == workflow_id
        assert status_data["status"] in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]

        # 3. Cancel workflow
        resp_cancel = await client.post(f"/api/v1/investigations/workflow/{workflow_id}/cancel")
        assert resp_cancel.status_code == 200
        cancel_data = resp_cancel.json()
        assert cancel_data["status"] == "CANCELLED"

        # 4. Resume workflow
        resp_resume = await client.post(f"/api/v1/investigations/workflow/{workflow_id}/resume")
        assert resp_resume.status_code == 200
