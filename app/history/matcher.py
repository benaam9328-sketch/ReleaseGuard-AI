import json
from pathlib import Path

from app.schemas.enums import SourceStatus
from app.schemas.evidence import HistoryEvidence, ReleaseEvidence, ReleaseEvidenceSubmit

_CATALOG = Path(__file__).with_name("synthetic_records.json")


def load_synthetic_records(path: Path | None = None) -> list[dict]:
    catalog = path or _CATALOG
    if not catalog.exists():
        return []
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return payload.get("records") or []


def _same_repo(evidence: ReleaseEvidence, record: dict) -> bool:
    repository = record.get("repository")
    if not repository:
        return True
    return repository == evidence.repository or repository == evidence.service


def _is_similar(evidence: ReleaseEvidence, record: dict) -> bool:
    if not _same_repo(evidence, record):
        return False
    if record.get("database_migration") is True:
        if evidence.github.database_migration_detected is True:
            return True
    if (record.get("critical_vulnerabilities") or 0) >= 1:
        if (evidence.trivy.critical or 0) >= 1:
            return True
    if (record.get("high_vulnerabilities") or 0) >= 1:
        if (evidence.trivy.high or 0) >= 1:
            return True
    return False


def match_records(evidence: ReleaseEvidence, records: list[dict]) -> HistoryEvidence:
    if not records:
        return HistoryEvidence(status=SourceStatus.unknown)

    matches = [record for record in records if _is_similar(evidence, record)]
    synthetic = any(record.get("is_synthetic") is True for record in records)
    if not matches:
        return HistoryEvidence(
            status=SourceStatus.success,
            similar_historical_failure=False,
            rollback_required_recently=False,
            is_synthetic=synthetic,
        )

    rollback = any(record.get("outcome") == "rollback" for record in matches)
    return HistoryEvidence(
        status=SourceStatus.success,
        similar_historical_failure=True,
        rollback_required_recently=rollback,
        is_synthetic=synthetic,
        matched_record_ids=[
            str(record["record_id"]) for record in matches if record.get("record_id")
        ],
    )


def apply_history(
    evidence: ReleaseEvidence,
    submit: ReleaseEvidenceSubmit,
    records: list[dict] | None = None,
) -> ReleaseEvidence:
    if submit.history is not None:
        return evidence
    catalog = records if records is not None else load_synthetic_records()
    evidence.history = match_records(evidence, catalog)
    return evidence
