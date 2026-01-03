import pytest  # noqa: F401
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_quality_endpoint():
    response = client.get("/api/quality-metrics")
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert isinstance(data["overall_score"], (int, float))
