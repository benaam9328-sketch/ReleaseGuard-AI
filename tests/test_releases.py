from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import store


def _client() -> TestClient:
    store.reset_memory()
    store.backend = "memory"
    store._session_factory = None
    return TestClient(create_app())


def test_submit_compact_and_fetch() -> None:
    client = _client()
    response = client.post(
        "/v1/releases",
        json={
            "release_id": "REL-001",
            "repository": "releaseguard-ai",
            "commit_sha": "abc123def456",
            "ci_status": "success",
            "test_status": "success",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 2,
        },
    )
    assert response.status_code == 201
    body = response.json()
    evidence = body["evidence"]
    assessment = body["assessment"]
    assert evidence["release_id"] == "REL-001"
    assert evidence["github"]["status"] == "unknown"
    assert evidence["github_actions"]["ci_status"] == "success"
    assert evidence["trivy"]["high"] == 2
    assert "github" in evidence["missing_sources"]
    assert assessment["release_id"] == "REL-001"
    assert assessment["enforcement"] == "none"
    assert "high_vulnerability" in [item["signal"] for item in assessment["signals"]]
    assert "missing_critical_evidence" in [
        item["signal"] for item in assessment["signals"]
    ]

    fetched = client.get("/v1/releases/REL-001")
    assert fetched.status_code == 200
    assert fetched.json()["release_id"] == "REL-001"

    scored = client.get("/v1/releases/REL-001/assessment")
    assert scored.status_code == 200
    assert scored.json()["risk_score"] == assessment["risk_score"]


def test_unknown_release_assessment_is_404() -> None:
    client = _client()
    response = client.get("/v1/releases/REL-missing/assessment")
    assert response.status_code == 404
    assert response.json()["detail"] == "release_not_found"


def test_missing_identity_is_422() -> None:
    client = _client()
    response = client.post(
        "/v1/releases",
        json={"ci_status": "success"},
    )
    assert response.status_code == 422


def test_failed_status_is_not_coerced() -> None:
    client = _client()
    response = client.post(
        "/v1/releases",
        json={
            "release_id": "REL-fail",
            "repository": "releaseguard-ai",
            "commit_sha": "abc123",
            "ci_status": "failure",
            "test_status": "unknown",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
        },
    )
    assert response.status_code == 201
    actions = response.json()["evidence"]["github_actions"]
    assert actions["ci_status"] == "failure"
    assert actions["test_status"] == "unknown"
    assert actions["status"] == "failure"
