"""Contract Testing and API Robustness validation across all REST endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_rejects_malformed_json_and_invalid_uuids(async_client: AsyncClient):
    """Verify API returns 422 Unprocessable Entity on non-UUID path parameters."""
    res = await async_client.get("/api/v1/projects/not-a-valid-uuid")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_api_returns_404_for_nonexistent_resources(async_client: AsyncClient):
    """Verify API returns 404 Not Found for nonexistent project or analysis IDs."""
    random_id = uuid4()
    res = await async_client.get(f"/api/v1/projects/{random_id}")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert f"Project with ID '{random_id}' not found" in data["detail"]


@pytest.mark.asyncio
async def test_api_rejects_missing_required_fields_on_project_create(async_client: AsyncClient):
    """Verify API rejects project creation when name is missing or empty."""
    res = await async_client.post("/api/v1/projects", json={})
    assert res.status_code == 422

    res_empty = await async_client.post("/api/v1/projects", json={"name": ""})
    # Empty string should fail min_length validation
    assert res_empty.status_code == 422


@pytest.mark.asyncio
async def test_api_analysis_status_conflict_returns_409(async_client: AsyncClient):
    """Verify API returns 409 Conflict when optimistic locking version is mismatched."""
    # 1. Create a project
    create_proj = await async_client.post(
        "/api/v1/projects",
        json={"name": "Robustness Project", "description": "For 409 test"},
    )
    assert create_proj.status_code == 201
    proj_id = create_proj.json()["id"]

    # 2. Create analysis session
    create_ana = await async_client.post(
        "/api/v1/analyses",
        json={
            "project_id": proj_id,
            "version_a_name": "v1.0",
            "version_a_url": "http://localhost:3000",
            "version_b_name": "v1.1",
            "version_b_url": "http://localhost:3001",
        },
    )
    assert create_ana.status_code == 201
    analysis_id = create_ana.json()["id"]

    # 3. Update status with mismatching version (expect 409)
    conflict_res = await async_client.patch(
        f"/api/v1/analyses/{analysis_id}/status",
        json={"current_version": 999, "status": "running"},
    )
    assert conflict_res.status_code == 409
    assert "conflict" in conflict_res.json()["detail"].lower()
