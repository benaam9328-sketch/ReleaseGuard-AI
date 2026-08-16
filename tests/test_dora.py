from datetime import datetime, timedelta, timezone

from app.dora.metrics import calculate_dora
from app.schemas.enums import EventType, SourceName
from app.schemas.events import DeliveryEvent

AS_OF = datetime(2026, 8, 16, 18, 0, tzinfo=timezone.utc)


def _event(
    event_id: str,
    event_type: EventType,
    timestamp: datetime,
    release_id: str | None = None,
    environment: str | None = "production",
    metadata: dict | None = None,
) -> DeliveryEvent:
    return DeliveryEvent(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        service="releaseguard-ai",
        release_id=release_id,
        environment=environment,
        source=SourceName.synthetic,
        is_synthetic=True,
        metadata=metadata or {},
    )


def test_empty_events_are_unavailable_not_zero() -> None:
    snapshot = calculate_dora([], AS_OF)
    assert snapshot.window.deployment_frequency.unavailable is True
    assert snapshot.window.deployment_frequency.value is None
    assert snapshot.window.lead_time_for_changes.unavailable is True
    assert snapshot.window.change_failure_rate.unavailable is True
    assert snapshot.window.time_to_restore_service.unavailable is True


def test_ten_deployments_in_30_days() -> None:
    events = []
    for index in range(10):
        day = 16 - index
        events.append(
            _event(
                f"dep-{index}",
                EventType.DEPLOYMENT,
                datetime(2026, 8, day, 12, 0, tzinfo=timezone.utc),
                release_id=f"REL-{index:03d}",
                metadata={"deployment_status": "success", "commit_sha": f"sha{index}"},
            )
        )
    snapshot = calculate_dora(events, AS_OF)
    metric = snapshot.window.deployment_frequency
    assert metric.unavailable is False
    assert metric.event_count == 10
    assert metric.value == 10 / 30
    assert metric.unit == "deployments_per_day"
    assert snapshot.trend.deployment_frequency.event_count == 7


def test_lead_time_is_eight_hours() -> None:
    events = [
        _event(
            "code-1",
            EventType.CODE_CHANGE,
            datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc),
            release_id="REL-104",
            environment=None,
            metadata={
                "commit_sha": "aaa111",
                "pull_request_number": 12,
                "is_first_commit_in_pr": True,
            },
        ),
        _event(
            "dep-1",
            EventType.DEPLOYMENT,
            datetime(2026, 8, 16, 18, 0, tzinfo=timezone.utc),
            release_id="REL-104",
            metadata={"deployment_status": "success", "commit_sha": "abc123"},
        ),
    ]
    snapshot = calculate_dora(events, AS_OF)
    metric = snapshot.window.lead_time_for_changes
    assert metric.unavailable is False
    assert metric.event_count == 1
    assert metric.value == 8.0
    assert metric.unit == "hours"


def test_missing_deploy_does_not_make_lead_time_zero() -> None:
    events = [
        _event(
            "code-1",
            EventType.CODE_CHANGE,
            datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc),
            release_id="REL-104",
            environment=None,
            metadata={"is_first_commit_in_pr": True, "commit_sha": "aaa111"},
        )
    ]
    metric = calculate_dora(events, AS_OF).window.lead_time_for_changes
    assert metric.unavailable is True
    assert metric.value is None


def test_cfr_is_15_percent_and_dedupes_failure_outcomes() -> None:
    events = []
    for index in range(20):
        events.append(
            _event(
                f"dep-{index}",
                EventType.DEPLOYMENT,
                datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
                + timedelta(hours=index),
                release_id=f"REL-{index:03d}",
                metadata={"deployment_status": "success", "commit_sha": f"sha{index}"},
            )
        )
    events[0].metadata["deployment_status"] = "failure"
    events.append(
        _event(
            "rb-1",
            EventType.ROLLBACK,
            datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
            release_id="REL-001",
            metadata={"rolled_back_release_id": "REL-001"},
        )
    )
    events.append(
        _event(
            "inc-1",
            EventType.INCIDENT_START,
            datetime(2026, 8, 2, 13, 0, tzinfo=timezone.utc),
            release_id="REL-001",
            metadata={
                "incident_id": "INC-1",
                "attribution_method": "explicit_release_id",
                "attribution_confidence": "attributed",
            },
        )
    )
    events.append(
        _event(
            "inc-2",
            EventType.INCIDENT_START,
            datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
            release_id="REL-002",
            metadata={
                "incident_id": "INC-2",
                "attribution_method": "explicit_release_id",
                "attribution_confidence": "attributed",
            },
        )
    )
    metric = calculate_dora(events, AS_OF).window.change_failure_rate
    assert metric.unavailable is False
    assert metric.event_count == 20
    assert metric.value == 15.0
    assert metric.unit == "percent"


def test_likely_related_incident_does_not_count_as_cfr() -> None:
    deploy_at = datetime(2026, 8, 16, 14, 0, tzinfo=timezone.utc)
    events = [
        _event(
            "dep-1",
            EventType.DEPLOYMENT,
            deploy_at,
            release_id="REL-104",
            metadata={"deployment_status": "success"},
        ),
        _event(
            "inc-1",
            EventType.INCIDENT_START,
            datetime(2026, 8, 16, 14, 8, tzinfo=timezone.utc),
            metadata={
                "incident_id": "INC-55",
                "attribution_method": "timestamp_correlation",
                "attribution_confidence": "likely_related",
            },
        ),
    ]
    metric = calculate_dora(events, AS_OF).window.change_failure_rate
    assert metric.value == 0.0
    assert metric.event_count == 1


def test_mttr_is_40_minutes() -> None:
    events = [
        _event(
            "inc-start",
            EventType.INCIDENT_START,
            datetime(2026, 8, 16, 14, 10, tzinfo=timezone.utc),
            release_id="REL-104",
            metadata={
                "incident_id": "INC-55",
                "attribution_method": "explicit_release_id",
                "attribution_confidence": "attributed",
            },
        ),
        _event(
            "inc-end",
            EventType.SERVICE_RESTORED,
            datetime(2026, 8, 16, 14, 50, tzinfo=timezone.utc),
            metadata={"incident_id": "INC-55"},
        ),
    ]
    metric = calculate_dora(events, AS_OF).window.time_to_restore_service
    assert metric.unavailable is False
    assert metric.event_count == 1
    assert metric.value == 40.0
    assert metric.unit == "minutes"


def test_open_incident_is_unavailable_not_zero() -> None:
    events = [
        _event(
            "inc-start",
            EventType.INCIDENT_START,
            datetime(2026, 8, 16, 14, 10, tzinfo=timezone.utc),
            metadata={"incident_id": "INC-55"},
        )
    ]
    metric = calculate_dora(events, AS_OF).window.time_to_restore_service
    assert metric.unavailable is True
    assert metric.value is None


def test_reversed_restore_is_excluded() -> None:
    events = [
        _event(
            "inc-start",
            EventType.INCIDENT_START,
            datetime(2026, 8, 16, 14, 50, tzinfo=timezone.utc),
            metadata={"incident_id": "INC-55"},
        ),
        _event(
            "inc-end",
            EventType.SERVICE_RESTORED,
            datetime(2026, 8, 16, 14, 10, tzinfo=timezone.utc),
            metadata={"incident_id": "INC-55"},
        ),
    ]
    snapshot = calculate_dora(events, AS_OF)
    metric = snapshot.window.time_to_restore_service
    assert metric.unavailable is True
    assert any("INC-55" in item for item in metric.validation_errors)


def test_dora_api_empty_is_unavailable() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.storage import store

    store.reset_memory()
    store.backend = "memory"
    client = TestClient(create_app())
    response = client.get("/v1/dora")
    assert response.status_code == 200
    body = response.json()
    assert body["window"]["deployment_frequency"]["unavailable"] is True
    assert body["window"]["deployment_frequency"]["value"] is None


def test_post_event_and_assessment_keeps_risk_score() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.storage import store

    store.reset_memory()
    store.backend = "memory"
    client = TestClient(create_app())
    created = client.post(
        "/v1/events",
        json={
            "event_id": "dep-now",
            "event_type": "DEPLOYMENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "releaseguard-ai",
            "release_id": "REL-001",
            "environment": "production",
            "source": "synthetic",
            "is_synthetic": True,
            "metadata": {"deployment_status": "success"},
        },
    )
    assert created.status_code == 201

    scored = client.post(
        "/v1/releases",
        json={
            "release_id": "REL-001",
            "repository": "releaseguard-ai",
            "commit_sha": "abc123def456",
            "ci_status": "success",
            "test_status": "success",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
        },
    )
    assert scored.status_code == 201
    assessment = scored.json()["assessment"]
    snapshot = assessment["dora_context"]["snapshot"]
    assert snapshot["window"]["deployment_frequency"]["event_count"] == 1
    assert assessment["risk_score"] == scored.json()["assessment"]["risk_score"]
    assert "dora" not in [
        item["signal"] for item in assessment["signals"]
    ]
