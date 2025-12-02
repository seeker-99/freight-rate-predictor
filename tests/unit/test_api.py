# tests/unit/test_api.py
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Freight Rate Prediction API"


def test_health_endpoint_exists():
    resp = client.get("/health")
    # While DB may be up or down, endpoint must respond
    assert resp.status_code in (200, 503)


def test_predict_endpoint():
    resp = client.get("/api/predict?route=NYC-LA&weight_kg=1500")
    assert resp.status_code == 200
    data = resp.json()
    assert data["route"] == "NYC-LA"
    assert data["weight_kg"] == 1500
    assert "predicted_rate" in data
    assert "total_cost" in data


def test_bulk_predict_endpoint():
    resp = client.post(
        "/api/bulk-predict?routes=NYC-LA&routes=NYC-CHI&weight_kg=1500"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["weight_kg"] == 1500
    assert len(data["predictions"]) >= 1
