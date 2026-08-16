from datetime import datetime, timezone

from app.normalize import expand_release_evidence
from app.risk.engine import assess
from app.schemas.enums import (
    Recommendation,
    RiskLevel,
    ScanStatus,
    SignalId,
    SourceStatus,
)
from app.schemas.evidence import (
    ChangedFile,
    GithubEvidence,
    HistoryEvidence,
    InfrastructureEvidence,
    ReleaseEvidenceSubmit,
    TrivyEvidence,
    TrivyFinding,
)


def _expand(**kwargs) -> object:
    payload = {
        "release_id": "REL-001",
        "repository": "releaseguard-ai",
        "commit_sha": "abc123def456",
        **kwargs,
    }
    return expand_release_evidence(ReleaseEvidenceSubmit(**payload))


def test_contract_high_risk_example_scores_75() -> None:
    first = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    evidence = _expand(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first,
            head_commit_sha="abc123def456",
            head_commit_at=head,
            changed_files_count=28,
            lines_changed=640,
            changed_files=[
                ChangedFile(path="app/main.py", change_type="modified"),
                ChangedFile(
                    path="alembic/versions/20260816_add_approvals.py",
                    change_type="added",
                ),
            ],
            database_migration_detected=True,
        ),
        github_actions=None,
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        trivy=TrivyEvidence(
            status=SourceStatus.success,
            scan_status=ScanStatus.findings,
            critical=1,
            high=0,
            findings=[
                TrivyFinding(
                    vulnerability_id="CVE-2024-0001",
                    severity="CRITICAL",
                    package="example-lib",
                )
            ],
        ),
        history=HistoryEvidence(
            status=SourceStatus.success,
            similar_historical_failure=True,
        ),
    )

    result = assess(evidence)
    ids = {item.signal for item in result.signals}
    assert SignalId.critical_vulnerability in ids
    assert SignalId.database_migration in ids
    assert SignalId.similar_historical_failure in ids
    assert SignalId.large_change_surface in ids
    assert result.risk_score == 75
    assert result.risk_level == RiskLevel.HIGH
    assert result.recommendation == Recommendation.BLOCK_APPROVAL_REQUIRED
    assert result.enforcement == "none"
    assert result.approval.state.value == "pending"


def test_ci_failure_and_rollback_dedupe_to_30() -> None:
    evidence = _expand(
        ci_status=SourceStatus.failure,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
        history=HistoryEvidence(
            status=SourceStatus.success,
            rollback_required_recently=True,
        ),
    )
    result = assess(evidence)
    groups = [item.deduplication_group.value for item in result.signals]
    assert groups.count("delivery_failure") == 1
    delivery = next(
        item for item in result.signals if item.deduplication_group.value == "delivery_failure"
    )
    assert delivery.weight == 30


def test_failed_trivy_scan_is_missing_evidence_not_clean() -> None:
    evidence = _expand(
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        trivy=TrivyEvidence(
            status=SourceStatus.unknown,
            scan_status=ScanStatus.scan_failed,
        ),
    )
    result = assess(evidence)
    ids = {item.signal for item in result.signals}
    assert SignalId.critical_vulnerability not in ids
    assert SignalId.high_vulnerability not in ids
    assert SignalId.missing_critical_evidence in ids


def test_unknown_ci_is_not_treated_as_failure() -> None:
    evidence = _expand(
        ci_status=SourceStatus.unknown,
        test_status=SourceStatus.unknown,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
    )
    result = assess(evidence)
    ids = {item.signal for item in result.signals}
    assert SignalId.ci_failure not in ids
    assert SignalId.missing_critical_evidence in ids


def test_multiple_high_cves_fire_once() -> None:
    first = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    evidence = _expand(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first,
            head_commit_sha="abc123def456",
            head_commit_at=head,
            changed_files_count=2,
            database_migration_detected=False,
        ),
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        trivy=TrivyEvidence(
            status=SourceStatus.success,
            scan_status=ScanStatus.findings,
            critical=0,
            high=3,
            findings=[
                TrivyFinding(vulnerability_id="CVE-1", severity="HIGH"),
                TrivyFinding(vulnerability_id="CVE-2", severity="HIGH"),
                TrivyFinding(vulnerability_id="CVE-3", severity="HIGH"),
            ],
        ),
    )
    result = assess(evidence)
    high_signals = [
        item for item in result.signals if item.signal == SignalId.high_vulnerability
    ]
    assert len(high_signals) == 1
    assert high_signals[0].weight == 15


def test_score_is_capped_at_100() -> None:
    first = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    evidence = _expand(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first,
            head_commit_sha="abc123def456",
            head_commit_at=head,
            changed_files_count=40,
            lines_changed=900,
            database_migration_detected=True,
        ),
        ci_status=SourceStatus.failure,
        test_status=SourceStatus.failure,
        trivy=TrivyEvidence(
            status=SourceStatus.success,
            scan_status=ScanStatus.findings,
            critical=2,
            high=4,
        ),
        infrastructure=InfrastructureEvidence(
            status=SourceStatus.success,
            high_risk_change_detected=True,
        ),
        history=HistoryEvidence(
            status=SourceStatus.success,
            similar_historical_failure=True,
            rollback_required_recently=True,
        ),
    )
    result = assess(evidence)
    assert result.risk_score == 100
    assert result.risk_level == RiskLevel.HIGH


def test_medium_band_requires_review() -> None:
    first = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    evidence = _expand(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first,
            head_commit_sha="abc123def456",
            head_commit_at=head,
            changed_files_count=25,
            database_migration_detected=True,
        ),
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=2,
    )
    result = assess(evidence)
    assert result.risk_score == 40
    assert result.risk_level == RiskLevel.MEDIUM
    assert result.recommendation == Recommendation.REQUIRE_HUMAN_REVIEW


def test_low_band_allows() -> None:
    first = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    evidence = _expand(
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first,
            head_commit_sha="abc123def456",
            head_commit_at=head,
            changed_files_count=2,
            database_migration_detected=False,
        ),
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
    )
    result = assess(evidence)
    assert result.risk_score == 0
    assert result.risk_level == RiskLevel.LOW
    assert result.recommendation == Recommendation.ALLOW

