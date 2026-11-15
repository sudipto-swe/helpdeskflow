"""Unit test for Analytics API endpoint."""
from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_analytics_summary_endpoint():
    client = TestClient(app)
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_tickets" in data
    assert "auto_resolution_rate" in data
    assert "policy_violation_rate" in data
    assert data["policy_violation_rate"] == 0.0
    assert "category_distribution" in data
