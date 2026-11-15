"""Unit tests for /health and /ready endpoints."""
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "helpdeskflow-api"
    assert "X-Request-ID" in response.headers


def test_readiness_check(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert "llm_provider" in data
