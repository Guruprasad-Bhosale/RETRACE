"""Integration tests for replay and compare API endpoints."""

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.v1.investigations import seed_sample_investigations

client = TestClient(app)


def test_api_replay_investigation_success():
    """Verify POST /api/v1/investigations/{id}/replay returns a valid reproducible replay result."""
    seed_sample_investigations()
    response = client.post("/api/v1/investigations/inv_comm_cart_01/replay")

    assert response.status_code == 200
    data = response.json()
    assert data["investigation_id"] == "inv_comm_cart_01"
    assert data["status"] == "REPRODUCIBLE"
    assert data["is_reproducible"] is True
    assert len(data["snapshot_hash"]) == 64
    assert len(data["graph_hash"]) == 64
    assert len(data["hypothesis_hash"]) == 64
    assert len(data["explanation_hash"]) == 64
    assert data["replayed_explanation"] is not None


def test_api_replay_investigation_not_found():
    """Verify POST /api/v1/investigations/{id}/replay returns 404 for unknown ID."""
    response = client.post("/api/v1/investigations/inv_nonexistent_999/replay")
    assert response.status_code == 404


def test_api_compare_investigations_success():
    """Verify GET /api/v1/investigations/{id}/compare/{other_id} returns comparison results."""
    seed_sample_investigations()
    response = client.get("/api/v1/investigations/inv_comm_cart_01/compare/inv_comm_modal_02")

    assert response.status_code == 200
    data = response.json()
    assert data["investigation_a_id"] == "inv_comm_cart_01"
    assert data["investigation_b_id"] == "inv_comm_modal_02"
    assert "graph_diff" in data
    assert data["root_cause_matches"] is False


def test_api_compare_investigations_not_found():
    """Verify GET /api/v1/investigations/{id}/compare/{other_id} returns 404 if either is missing."""
    response = client.get("/api/v1/investigations/inv_comm_cart_01/compare/inv_missing_999")
    assert response.status_code == 404
