"""Test Uncertainty-Time Tracking Integration"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for src module
BACKEND_DIR = Path(__file__).parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from src.uncertainty_map_v3 import UncertaintyMapV3

# Create test uncertainty map
test_uncertainty_map = UncertaintyMapV3(project_name="test-project")


@pytest.fixture
def client():
    """Create test client with dependency override"""
    from app.routers.uncertainty import get_uncertainty_map
    from main import app

    def get_test_uncertainty_map():
        return test_uncertainty_map

    app.dependency_overrides[get_uncertainty_map] = get_test_uncertainty_map

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_uncertainty_health(client):
    """Test uncertainty health endpoint works"""
    response = client.get("/api/uncertainty/health")
    assert response.status_code == 200
    data = response.json()
    # Health check endpoint doesn't use dependency injection, so it shows unavailable
    # We just verify it returns a valid response
    assert "status" in data


def test_track_with_uncertainty(client):
    """Test uncertainty-aware tracking endpoint"""
    payload = {
        "task_id": "test_integration_001",
        "task_type": "implementation",
        "phase": "implementation",
        "ai_used": "claude",
        "uncertainty_context": {
            "phase": "implementation",
            "has_code": True,
            "validation_score": 0.7,
            "team_size": 3,
            "timeline_weeks": 8,
        },
        "metadata": {"test": "uncertainty_integration"},
    }

    response = client.post("/api/uncertainty/track-with-uncertainty", json=payload)

    # Print response for debugging
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")

    # Check status code
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"

    # Check response structure
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data
    assert "baseline_seconds" in data
    assert "adjusted_baseline_seconds" in data
    assert "uncertainty_vector" in data
    assert "uncertainty_state" in data
    assert "confidence_score" in data
    assert "risk_factors" in data

    # Verify uncertainty-based adjustment
    assert data["adjusted_baseline_seconds"] >= data["baseline_seconds"]
    assert 0 <= data["confidence_score"] <= 1


def test_adjusted_baseline(client):
    """Test adjusted baseline endpoint"""
    payload = {
        "phase": "implementation",
        "has_code": True,
        "validation_score": 0.7,
        "team_size": 3,
        "timeline_weeks": 8,
    }

    response = client.post(
        "/api/uncertainty/adjusted-baseline/implementation/implementation", json=payload
    )

    # Print response for debugging
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")

    # Check status code
    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"

    # Check response structure
    data = response.json()
    assert "standard_baseline_seconds" in data
    assert "adjusted_baseline_seconds" in data
    assert "adjustment_percentage" in data
    assert "confidence_score" in data
    assert "confidence_interval_lower" in data
    assert "confidence_interval_upper" in data
    assert "adjustment_factors" in data
