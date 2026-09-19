"""Integration tests for Projects and Analyses API v1 endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_endpoints(async_client: AsyncClient):
    # 1. Create Project
    create_payload = {
        "name": "Integration Test Project",
        "description": "Created during automated integration test",
    }
    create_res = await async_client.post("/api/v1/projects", json=create_payload)
    assert create_res.status_code == 201
    project = create_res.json()
    assert project["name"] == "Integration Test Project"
    project_id = project["id"]

    # 2. Get Project
    get_res = await async_client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 3. Create Version
    ver_payload = {
        "name": "Release v1.0",
        "base_url": "http://localhost:3000",
        "git_commit_hash": "a1b2c3d",
    }
    ver_res = await async_client.post(f"/api/v1/projects/{project_id}/versions", json=ver_payload)
    assert ver_res.status_code == 201
    version = ver_res.json()
    assert version["name"] == "Release v1.0"

    # 4. List Project Versions
    list_ver_res = await async_client.get(f"/api/v1/projects/{project_id}/versions")
    assert list_ver_res.status_code == 200
    assert len(list_ver_res.json()) >= 1

    # 5. List Projects
    list_res = await async_client.get("/api/v1/projects")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_analysis_lifecycle_and_optimistic_locking_endpoint(async_client: AsyncClient):
    # 1. Start Analysis
    project_id = str(uuid4())
    payload = {
        "project_id": project_id,
        "version_a_name": "Baseline (v1.0)",
        "version_a_url": "http://localhost:3001",
        "version_b_name": "Candidate (v1.1)",
        "version_b_url": "http://localhost:3002",
        "config": {"timeout_seconds": 60},
    }
    res = await async_client.post("/api/v1/analyses", json=payload)
    assert res.status_code == 201
    analysis = res.json()
    assert analysis["status"] == "pending"
    assert analysis["version"] == 1
    analysis_id = analysis["id"]

    # 2. Update Status with matching version: 1 -> 2
    update_payload = {
        "current_version": 1,
        "status": "running",
    }
    update_res = await async_client.patch(
        f"/api/v1/analyses/{analysis_id}/status", json=update_payload
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "running"
    assert updated["version"] == 2

    # 3. Update Status with stale version 1 (Expect 409 Conflict)
    conflict_payload = {
        "current_version": 1,
        "status": "completed",
    }
    conflict_res = await async_client.patch(
        f"/api/v1/analyses/{analysis_id}/status", json=conflict_payload
    )
    assert conflict_res.status_code == 409

    # 4. Get Analysis
    get_res = await async_client.get(f"/api/v1/analyses/{analysis_id}")
    assert get_res.status_code == 200
    assert get_res.json()["version"] == 2
