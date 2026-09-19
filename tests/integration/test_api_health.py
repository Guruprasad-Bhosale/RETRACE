"""Integration tests for Health and System status endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_liveness(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "retrace-api"
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers


@pytest.mark.asyncio
async def test_ready_endpoint(async_client: AsyncClient):
    response = await async_client.get("/ready")
    # Response code is 200 if ready or 503 if dependencies disconnected (e.g. without live DB in unit/ci run)
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_system_status(async_client: AsyncClient):
    response = await async_client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["api_status"] == "online"
    assert "storage_backend" in data
