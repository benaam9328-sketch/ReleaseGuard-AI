from datetime import datetime, timedelta, timezone

from app.adapters.enrich import enrich_release_evidence
from app.config import Settings
from app.history.matcher import apply_history
from app.normalize import expand_release_evidence
from app.schemas.enums import EventType, SourceName, SourceStatus
from app.schemas.events import DeliveryEvent
from app.schemas.evidence import ReleaseEvidence, ReleaseEvidenceSubmit
from app.storage import EvidenceStore


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


def demo_events(release_id: str, now: datetime) -> list[DeliveryEvent]:
    first = now - timedelta(hours=8)
    events = [
        _event(
            "demo-code-1",
            EventType.CODE_CHANGE,
            first,
            release_id=release_id,
            environment=None,
            metadata={
                "commit_sha": "aaa111",
                "pull_request_number": 12,
                "is_first_commit_in_pr": True,
            },
        ),
        _event(
            "demo-dep-head",
            EventType.DEPLOYMENT,
            now,
            release_id=release_id,
            metadata={"deployment_status": "success", "commit_sha": "abc123def456"},
        ),
        _event(
            "demo-inc-start",
            EventType.INCIDENT_START,
            now - timedelta(days=2, hours=1),
            release_id="REL-old",
            metadata={
                "incident_id": "INC-DEMO",
                "attribution_method": "explicit_release_id",
                "attribution_confidence": "attributed",
            },
        ),
        _event(
            "demo-inc-end",
            EventType.SERVICE_RESTORED,
            now - timedelta(days=2, hours=0, minutes=20),
            metadata={"incident_id": "INC-DEMO"},
        ),
    ]
    for index in range(8):
        events.append(
            _event(
                f"demo-dep-{index}",
                EventType.DEPLOYMENT,
                now - timedelta(days=index + 1),
                release_id=f"REL-old-{index}",
                metadata={"deployment_status": "success"},
            )
        )
    events.append(
        _event(
            "demo-dep-fail",
            EventType.DEPLOYMENT,
            now - timedelta(days=3),
            release_id="REL-old",
            metadata={"deployment_status": "failure"},
        )
    )
    return events


def seed_demo_release(
    store: EvidenceStore,
    settings: Settings,
    release_id: str,
    now: datetime | None = None,
) -> ReleaseEvidence:
    stamp = now or datetime.now(timezone.utc)
    for event in demo_events(release_id, stamp):
        store.save_event(event)

    submit = ReleaseEvidenceSubmit(
        release_id=release_id,
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=2,
        is_synthetic=True,
    )
    evidence = expand_release_evidence(submit)
    evidence = enrich_release_evidence(evidence, submit, settings)
    evidence = apply_history(evidence, submit)
    stored, _created = store.save(evidence)
    return stored
