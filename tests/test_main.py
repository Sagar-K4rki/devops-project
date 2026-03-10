from fastapi.testclient import TestClient
import os

# Tell the app to skip DB connection during tests
os.environ["TESTING"] = "true"

from app.main import app

client = TestClient(app)

def test_root():
    """Tests that the root endpoint returns 200 OK"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_metrics_endpoint():
    """Tests that the metrics endpoint exists and returns data"""
    response = client.get("/metrics")
    assert response.status_code == 200

def test_health_endpoint_exists():
    """Tests that the health endpoint exists"""
    response = client.get("/health")
    # Will return 503 since no DB in test env, but endpoint exists
    assert response.status_code in [200, 503]