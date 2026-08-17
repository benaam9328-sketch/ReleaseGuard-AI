from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import store


def test_demo_seed_fills_dora() -> None:
    store.reset_memory()
    store.backend = "memory"
    client = TestClient(create_app())
    response = client.post("/v1/demo/seed", json={"release_id": "REL-demo"})
    assert response.status_code == 201
    body = response.json()
    dora = body["assessment"]["dora_context"]["snapshot"]["window"]
    assert dora["deployment_frequency"]["unavailable"] is False
    assert dora["deployment_frequency"]["event_count"] >= 1
    assert dora["lead_time_for_changes"]["unavailable"] is False
    assert dora["lead_time_for_changes"]["value"] == 8.0
    assert body["evidence"]["is_synthetic"] is True
    assert body["assessment"]["dora_context"]["snapshot"]["includes_synthetic"] is True
