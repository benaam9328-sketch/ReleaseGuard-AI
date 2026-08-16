from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import store


def _client() -> TestClient:
    store.reset_memory()
    store.backend = "memory"
    store._session_factory = None
    return TestClient(create_app())


def _submit(client: TestClient, release_id: str = "REL-001"):
    return client.post(
        "/v1/releases",
        json={
            "release_id": release_id,
            "repository": "releaseguard-ai",
            "commit_sha": "abc123def456",
            "ci_status": "success",
            "test_status": "success",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 2,
        },
    )


def test_approve_is_recorded_and_does_not_change_score():
    client = _client()
    created = _submit(client)
    original_score = created.json()["assessment"]["risk_score"]
    assert created.json()["assessment"]["approval"]["state"] == "pending"

    response = client.post(
        "/v1/releases/REL-001/approval",
        json={"decision": "approve"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["approval"]["state"] == "approved"
    assert body["approval"]["decision"] == "approve"
    assert body["approval"]["decided_at"] is not None
    assert body["risk_score"] == original_score
    assert body["enforcement"] == "none"

    fetched = client.get("/v1/releases/REL-001/assessment")
    assert fetched.json()["approval"]["state"] == "approved"
    assert fetched.json()["risk_score"] == original_score


def test_reject_is_recorded():
    client = _client()
    _submit(client, "REL-002")
    response = client.post(
        "/v1/releases/REL-002/approval",
        json={"decision": "reject"},
    )
    assert response.status_code == 200
    assert response.json()["approval"]["state"] == "rejected"
    assert response.json()["approval"]["decision"] == "reject"


def test_approval_unknown_release_is_404():
    client = _client()
    response = client.post(
        "/v1/releases/REL-missing/approval",
        json={"decision": "approve"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "release_not_found"


def test_invalid_decision_is_422():
    client = _client()
    _submit(client)
    response = client.post(
        "/v1/releases/REL-001/approval",
        json={"decision": "ship-it"},
    )
    assert response.status_code == 422
