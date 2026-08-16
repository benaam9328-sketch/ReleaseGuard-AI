from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import store


def test_health_ok():
    store.reset_memory()
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "releaseguard-ai"


def test_ready_memory():
    store.reset_memory()
    store.backend = "memory"
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["storage"] == "memory"
