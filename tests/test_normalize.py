from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.normalize import expand_release_evidence
from app.schemas.enums import ScanStatus, SourceStatus
from app.schemas.evidence import (
    GithubEvidence,
    ReleaseEvidenceSubmit,
    TrivyEvidence,
)


def test_compact_example_expands_without_inventing_github_details() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-001",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=2,
    )
    evidence = expand_release_evidence(submit)

    assert evidence.service == "releaseguard-ai"
    assert evidence.environment == "production"
    assert evidence.github.status == SourceStatus.unknown
    assert evidence.github.head_commit_sha == "abc123def456"
    assert evidence.github.changed_files_count is None
    assert "github" in evidence.missing_sources
    assert evidence.github_actions.ci_status == SourceStatus.success
    assert evidence.github_actions.test_status == SourceStatus.success
    assert evidence.trivy.scan_status == ScanStatus.findings
    assert evidence.trivy.critical == 0
    assert evidence.trivy.high == 2
    assert evidence.trivy.medium is None
    assert evidence.trivy.low is None
    assert "github_actions" not in evidence.missing_sources
    assert "trivy" not in evidence.missing_sources


def test_omitted_trivy_counts_are_unavailable_not_zero() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-002",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
    )
    evidence = expand_release_evidence(submit)
    assert evidence.trivy.scan_status == ScanStatus.unavailable
    assert evidence.trivy.critical is None
    assert evidence.trivy.high is None
    assert "trivy" in evidence.missing_sources


def test_clean_trivy_scan_keeps_explicit_zeros() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-003",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
    )
    evidence = expand_release_evidence(submit)
    assert evidence.trivy.scan_status == ScanStatus.clean
    assert evidence.trivy.critical == 0
    assert evidence.trivy.high == 0


def test_github_success_requires_contract_fields() -> None:
    with pytest.raises(ValidationError):
        GithubEvidence(
            status=SourceStatus.success,
            head_commit_sha="abc",
        )


def test_failed_trivy_scan_cannot_carry_zero_counts() -> None:
    with pytest.raises(ValidationError):
        TrivyEvidence(
            status=SourceStatus.unknown,
            scan_status=ScanStatus.scan_failed,
            critical=0,
            high=0,
        )


def test_canonical_github_success_keeps_provided_timestamps() -> None:
    first_commit_at = datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc)
    head_commit_at = datetime(2026, 8, 16, 16, 0, tzinfo=timezone.utc)
    submit = ReleaseEvidenceSubmit(
        release_id="REL-004",
        repository="releaseguard-ai",
        commit_sha="abc123def456",
        github=GithubEvidence(
            status=SourceStatus.success,
            first_commit_sha="aaa111",
            first_commit_at=first_commit_at,
            head_commit_sha="abc123def456",
            head_commit_at=head_commit_at,
            changed_files_count=28,
            database_migration_detected=True,
        ),
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=2,
    )
    # Nested github plus compact CI/Trivy fields is a valid partial submit.
    evidence = expand_release_evidence(submit)
    assert evidence.github.status == SourceStatus.success
    assert evidence.github.first_commit_sha == "aaa111"
    assert "github" not in evidence.missing_sources
    assert evidence.github_actions.ci_status == SourceStatus.success
    assert evidence.trivy.high == 2
