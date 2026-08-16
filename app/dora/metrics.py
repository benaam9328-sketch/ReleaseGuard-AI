from datetime import datetime, timedelta, timezone
from statistics import median

from app.risk.catalog import DORA_TREND_WINDOW_DAYS, DORA_WINDOW_DAYS
from app.schemas.dora import DoraMetric, DoraSnapshot, DoraWindow
from app.schemas.enums import AttributionConfidence, EventType
from app.schemas.events import DeliveryEvent


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _in_window(
    events: list[DeliveryEvent], as_of: datetime, days: int
) -> list[DeliveryEvent]:
    end = _aware(as_of)
    start = end - timedelta(days=days)
    selected = []
    for event in events:
        stamp = _aware(event.timestamp)
        if start <= stamp <= end:
            selected.append(event)
    return selected


def _unavailable(window_days: int, errors: list[str] | None = None) -> DoraMetric:
    return DoraMetric(
        unavailable=True,
        window_days=window_days,
        validation_errors=errors or [],
    )


def _deploy_key(event: DeliveryEvent) -> str:
    return event.release_id or event.event_id


def production_deployments(events: list[DeliveryEvent]) -> list[DeliveryEvent]:
    """Unique production deploys. Failure records for the same release count once."""
    by_key: dict[str, DeliveryEvent] = {}
    for event in events:
        if event.environment != "production":
            continue
        if event.event_type not in {EventType.DEPLOYMENT, EventType.DEPLOYMENT_FAILURE}:
            continue
        key = _deploy_key(event)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = event
            continue
        if (
            existing.event_type == EventType.DEPLOYMENT_FAILURE
            and event.event_type == EventType.DEPLOYMENT
        ):
            by_key[key] = event
    return list(by_key.values())


def _is_failed_deploy(event: DeliveryEvent) -> bool:
    if event.event_type == EventType.DEPLOYMENT_FAILURE:
        return True
    return event.metadata.get("deployment_status") == "failure"


def _is_success_deploy(event: DeliveryEvent) -> bool:
    return (
        event.event_type == EventType.DEPLOYMENT
        and event.environment == "production"
        and event.metadata.get("deployment_status") == "success"
    )


def _rollback_keys(events: list[DeliveryEvent]) -> set[str]:
    keys: set[str] = set()
    for event in events:
        if event.event_type != EventType.ROLLBACK:
            continue
        rolled = event.metadata.get("rolled_back_release_id") or event.release_id
        if rolled:
            keys.add(str(rolled))
    return keys


def _attributed_release_ids(events: list[DeliveryEvent]) -> set[str]:
    ids: set[str] = set()
    for event in events:
        if event.event_type != EventType.INCIDENT_START:
            continue
        confidence = event.metadata.get("attribution_confidence")
        if confidence != AttributionConfidence.attributed.value:
            continue
        if event.release_id:
            ids.add(event.release_id)
    return ids


def deployment_frequency(
    events: list[DeliveryEvent], as_of: datetime, window_days: int
) -> DoraMetric:
    if not events:
        return _unavailable(window_days)
    deploys = production_deployments(_in_window(events, as_of, window_days))
    count = len(deploys)
    return DoraMetric(
        unavailable=False,
        event_count=count,
        value=count / window_days,
        unit="deployments_per_day",
        window_days=window_days,
    )


def lead_time_for_changes(
    events: list[DeliveryEvent], as_of: datetime, window_days: int
) -> DoraMetric:
    if not events:
        return _unavailable(window_days)
    windowed = _in_window(events, as_of, window_days)
    first_by_release: dict[str, DeliveryEvent] = {}
    first_by_sha: dict[str, DeliveryEvent] = {}
    for event in events:
        if event.event_type != EventType.CODE_CHANGE:
            continue
        if event.metadata.get("is_first_commit_in_pr") is not True:
            continue
        if event.release_id and event.release_id not in first_by_release:
            first_by_release[event.release_id] = event
        sha = event.metadata.get("commit_sha")
        if sha and sha not in first_by_sha:
            first_by_sha[str(sha)] = event

    hours: list[float] = []
    errors: list[str] = []
    for deploy in windowed:
        if not _is_success_deploy(deploy):
            continue
        start = None
        if deploy.release_id:
            start = first_by_release.get(deploy.release_id)
        if start is None:
            sha = deploy.metadata.get("commit_sha")
            if sha:
                start = first_by_sha.get(str(sha))
        if start is None:
            continue
        delta = _aware(deploy.timestamp) - _aware(start.timestamp)
        if delta.total_seconds() < 0:
            errors.append(f"lead_time_reversed:{deploy.event_id}")
            continue
        hours.append(delta.total_seconds() / 3600)

    if not hours:
        return _unavailable(window_days, errors)
    return DoraMetric(
        unavailable=False,
        event_count=len(hours),
        value=float(median(hours)),
        unit="hours",
        window_days=window_days,
        validation_errors=errors,
    )


def change_failure_rate(
    events: list[DeliveryEvent], as_of: datetime, window_days: int
) -> DoraMetric:
    if not events:
        return _unavailable(window_days)
    deploys = production_deployments(_in_window(events, as_of, window_days))
    if not deploys:
        return _unavailable(window_days)
    rollback_keys = _rollback_keys(events)
    attributed = _attributed_release_ids(events)
    failed: set[str] = set()
    for deploy in deploys:
        key = _deploy_key(deploy)
        if _is_failed_deploy(deploy):
            failed.add(key)
        if key in rollback_keys:
            failed.add(key)
        if deploy.release_id and deploy.release_id in attributed:
            failed.add(key)
    return DoraMetric(
        unavailable=False,
        event_count=len(deploys),
        value=round(100.0 * len(failed) / len(deploys), 10),
        unit="percent",
        window_days=window_days,
    )


def time_to_restore_service(
    events: list[DeliveryEvent], as_of: datetime, window_days: int
) -> DoraMetric:
    if not events:
        return _unavailable(window_days)
    windowed = _in_window(events, as_of, window_days)
    starts: dict[str, DeliveryEvent] = {}
    for event in windowed:
        if event.event_type != EventType.INCIDENT_START:
            continue
        incident_id = event.metadata.get("incident_id")
        if incident_id:
            starts[str(incident_id)] = event

    restores: dict[str, DeliveryEvent] = {}
    for event in events:
        if event.event_type != EventType.SERVICE_RESTORED:
            continue
        incident_id = event.metadata.get("incident_id")
        if incident_id:
            restores[str(incident_id)] = event

    minutes: list[float] = []
    errors: list[str] = []
    for incident_id, start in starts.items():
        restore = restores.get(incident_id)
        if restore is None:
            continue
        delta = _aware(restore.timestamp) - _aware(start.timestamp)
        if delta.total_seconds() < 0:
            errors.append(f"mttr_reversed:{incident_id}")
            continue
        minutes.append(delta.total_seconds() / 60)

    if not minutes:
        return _unavailable(window_days, errors)
    return DoraMetric(
        unavailable=False,
        event_count=len(minutes),
        value=float(median(minutes)),
        unit="minutes",
        window_days=window_days,
        validation_errors=errors,
    )


def _window(
    events: list[DeliveryEvent], as_of: datetime, window_days: int
) -> DoraWindow:
    return DoraWindow(
        window_days=window_days,
        deployment_frequency=deployment_frequency(events, as_of, window_days),
        lead_time_for_changes=lead_time_for_changes(events, as_of, window_days),
        change_failure_rate=change_failure_rate(events, as_of, window_days),
        time_to_restore_service=time_to_restore_service(events, as_of, window_days),
    )


def calculate_dora(
    events: list[DeliveryEvent],
    as_of: datetime,
    window_days: int = DORA_WINDOW_DAYS,
    trend_window_days: int = DORA_TREND_WINDOW_DAYS,
) -> DoraSnapshot:
    return DoraSnapshot(
        window=_window(events, as_of, window_days),
        trend=_window(events, as_of, trend_window_days),
        includes_synthetic=any(event.is_synthetic for event in events),
    )
