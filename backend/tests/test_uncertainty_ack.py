"""Tests for mitigation ACK endpoint and status cache invalidation."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend can be imported
BACKEND_DIR = Path(__file__).parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from src.uncertainty_map_v3 import UncertaintyMapV3  # noqa: E402

# Create test uncertainty map instance
test_uncertainty_map = UncertaintyMapV3(project_name="test-project")


@pytest.fixture
def client():
    """Create test client with dependency override"""
    from app.routers.uncertainty import get_uncertainty_map
    from main import app

    def _override_uncertainty():
        return test_uncertainty_map

    app.dependency_overrides[get_uncertainty_map] = _override_uncertainty

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_status_and_ack_mitigation_reduces_magnitude(client):
    """Status should return mitigations, and ACK should reduce magnitude/increase confidence."""
    status_resp = client.get("/api/uncertainty/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    original_mag = status_data["vector"]["magnitude"]
    mitigations = status_data["mitigations"]
    assert mitigations, "Mitigations should be present in status response"

    target_id = mitigations[0]["id"]
    dominant = status_data["vector"]["dominant_dimension"]

    ack_resp = client.post(
        f"/api/uncertainty/ack/{target_id}",
        json={"mitigation_id": target_id, "dimension": dominant},
    )

    assert ack_resp.status_code == 200, ack_resp.text
    ack_data = ack_resp.json()
    assert ack_data["success"] is True
    assert ack_data["updated_vector"] is not None

    updated_mag = ack_data["updated_vector"]["magnitude"]
    updated_conf = ack_data["confidence_score"]

    # Magnitude should not increase; confidence should not decrease
    assert updated_mag <= original_mag
    assert updated_conf >= (1.0 - original_mag) - 1e-6
