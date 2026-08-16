from app.history.matcher import apply_history, match_records
from app.normalize import expand_release_evidence
from app.risk.engine import assess
from app.schemas.enums import SignalId, SourceStatus
from app.schemas.evidence import GithubEvidence, HistoryEvidence, ReleaseEvidenceSubmit


def _evidence(**kwargs):
    payload = {
        "release_id": "REL-200",
        "repository": "releaseguard-ai",
        "commit_sha": "abc123def456",
        "ci_status": SourceStatus.success,
        "test_status": SourceStatus.success,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 0,
        **kwargs,
    }
    return expand_release_evidence(ReleaseEvidenceSubmit(**payload))


def test_empty_catalog_leaves_history_unknown() -> None:
    evidence = _evidence()
    matched = match_records(evidence, [])
    assert matched.status == SourceStatus.unknown
    assert matched.similar_historical_failure is None
    result = assess(evidence.model_copy(update={"history": matched}))
    assert SignalId.similar_historical_failure not in [
        item.signal for item in result.signals
    ]


def test_migration_matches_labeled_synthetic_rollback() -> None:
    evidence = _evidence(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at="2026-08-16T09:00:00Z",
            head_commit_sha="abc123def456",
            head_commit_at="2026-08-16T16:00:00Z",
            changed_files_count=3,
            database_migration_detected=True,
        )
    )
    records = [
        {
            "record_id": "HIST-MIG-001",
            "repository": "releaseguard-ai",
            "outcome": "rollback",
            "database_migration": True,
            "is_synthetic": True,
            "summary": "Labeled demo: migration rollback",
        }
    ]
    matched = match_records(evidence, records)
    assert matched.status == SourceStatus.success
    assert matched.similar_historical_failure is True
    assert matched.rollback_required_recently is True
    assert matched.is_synthetic is True
    assert matched.matched_record_ids == ["HIST-MIG-001"]
    result = assess(evidence.model_copy(update={"history": matched}))
    assert SignalId.similar_historical_failure in [item.signal for item in result.signals]


def test_no_overlap_is_false_not_unknown() -> None:
    evidence = _evidence(high_vulnerabilities=2)
    records = [
        {
            "record_id": "HIST-MIG-001",
            "repository": "releaseguard-ai",
            "outcome": "rollback",
            "database_migration": True,
            "is_synthetic": True,
        }
    ]
    matched = match_records(evidence, records)
    assert matched.status == SourceStatus.success
    assert matched.similar_historical_failure is False
    assert matched.is_synthetic is True


def test_explicit_history_is_not_overwritten() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-201",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        history=HistoryEvidence(
            status=SourceStatus.success,
            similar_historical_failure=False,
            is_synthetic=True,
        ),
    )
    evidence = expand_release_evidence(submit)
    updated = apply_history(evidence, submit, records=[])
    assert updated.history.similar_historical_failure is False
    assert updated.history.status == SourceStatus.success
