"""Integration tests for Forensics & Evidence Graph 2.0 API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app


@pytest.mark.asyncio
async def test_get_evidence_graph_success():
    """Verify GET /api/v1/investigations/{id}/evidence-graph returns deterministic DAG."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch list of investigations to obtain valid ID
        list_res = await client.get("/api/v1/investigations")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) > 0
        inv_id = items[0]["investigation_id"]

        # 2. Fetch evidence graph
        res = await client.get(f"/api/v1/investigations/{inv_id}/evidence-graph")
        assert res.status_code == 200
        graph = res.json()

        assert graph["investigation_id"] == inv_id
        assert len(graph["nodes"]) >= 5
        assert len(graph["edges"]) >= 4
        assert graph["deterministic_hash"] != ""


@pytest.mark.asyncio
async def test_get_investigation_explanation_success():
    """Verify GET /api/v1/investigations/{id}/explanation returns full forensic explanation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_res = await client.get("/api/v1/investigations")
        inv_id = list_res.json()[0]["investigation_id"]

        res = await client.get(f"/api/v1/investigations/{inv_id}/explanation")
        assert res.status_code == 200
        data = res.json()

        assert data["investigation_id"] == inv_id
        assert "primary_hypothesis" in data
        assert len(data["eliminated_alternatives"]) >= 2
        assert "falsification" in data
        assert data["falsification"]["condition_id"].startswith("fals_")
        assert "confidence" in data
        assert data["confidence"]["level"] in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT")


@pytest.mark.asyncio
async def test_get_evidence_graph_404():
    """Verify non-existent investigation ID returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/investigations/non_existent_id_9999/evidence-graph")
        assert res.status_code == 404
