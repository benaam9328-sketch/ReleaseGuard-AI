from app.adapters.actions import actions_evidence_from_runs
from app.adapters.enrich import enrich_release_evidence
from app.adapters.github import github_evidence_from_commit
from app.adapters.trivy import parse_trivy_report
from app.config import Settings
from app.normalize import expand_release_evidence
from app.schemas.enums import ScanStatus, SourceStatus
from app.schemas.evidence import ReleaseEvidenceSubmit


def test_parse_trivy_report_counts_findings() -> None:
    report = {
        "Results": [
            {
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-0001",
                        "Severity": "HIGH",
                        "PkgName": "example-lib",
                        "Title": "Example",
                    },
                    {
                        "VulnerabilityID": "CVE-2024-0002",
                        "Severity": "CRITICAL",
                        "PkgName": "other-lib",
                    },
                ]
            }
        ]
    }
    trivy = parse_trivy_report(report)
    assert trivy.scan_status == ScanStatus.findings
    assert trivy.critical == 1
    assert trivy.high == 1
    assert trivy.medium == 0
    assert trivy.low == 0
    assert trivy.findings[0].vulnerability_id == "CVE-2024-0001"


def test_parse_trivy_empty_results_is_clean_not_unknown() -> None:
    trivy = parse_trivy_report({"Results": []})
    assert trivy.scan_status == ScanStatus.clean
    assert trivy.critical == 0
    assert trivy.high == 0


def test_parse_trivy_missing_results_is_scan_failed() -> None:
    trivy = parse_trivy_report({"SchemaVersion": 2})
    assert trivy.scan_status == ScanStatus.scan_failed
    assert trivy.critical is None
    assert trivy.high is None


def test_github_commit_payload_maps_files_and_migration() -> None:
    payload = {
        "sha": "abc123def456",
        "commit": {
            "author": {
                "name": "dev-a",
                "date": "2026-08-16T16:00:00Z",
            }
        },
        "stats": {"additions": 40, "deletions": 2},
        "files": [
            {"filename": "app/main.py", "status": "modified"},
            {
                "filename": "alembic/versions/20260816_add_approvals.py",
                "status": "added",
            },
        ],
    }
    github = github_evidence_from_commit("abc123def456", payload)
    assert github.status == SourceStatus.success
    assert github.changed_files_count == 2
    assert github.lines_changed == 42
    assert github.database_migration_detected is True
    assert github.first_commit_sha == "abc123def456"


def test_actions_maps_failed_run() -> None:
    runs = {
        "workflow_runs": [
            {
                "id": 99,
                "name": "ci",
                "conclusion": "failure",
                "run_started_at": "2026-08-16T16:00:00Z",
                "updated_at": "2026-08-16T16:03:00Z",
            }
        ]
    }
    jobs = {
        "jobs": [
            {"name": "build", "conclusion": "success"},
            {"name": "test", "conclusion": "failure"},
        ]
    }
    actions = actions_evidence_from_runs(runs, jobs)
    assert actions.ci_status == SourceStatus.failure
    assert actions.test_status == SourceStatus.failure
    assert actions.workflow_duration_seconds == 180


def test_enrich_uses_trivy_report_and_fake_github() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-010",
        repository="benaam9328-sketch/ReleaseGuard-AI",
        commit_sha="abc123def456",
        trivy_report={"Results": []},
    )
    evidence = expand_release_evidence(submit)

    def fake_get(url: str):
        if url.endswith("/commits/abc123def456"):
            return 200, {
                "commit": {
                    "author": {"name": "dev-a", "date": "2026-08-16T16:00:00Z"}
                },
                "stats": {"additions": 1, "deletions": 0},
                "files": [{"filename": "README.md", "status": "modified"}],
            }
        if url.endswith("/pulls"):
            return 200, []
        if "actions/runs" in url:
            return 200, {
                "workflow_runs": [
                    {
                        "id": 1,
                        "name": "ci",
                        "conclusion": "success",
                        "run_started_at": "2026-08-16T16:00:00Z",
                        "updated_at": "2026-08-16T16:01:00Z",
                    }
                ]
            }
        if url.endswith("/jobs"):
            return 200, {"jobs": [{"name": "test", "conclusion": "success"}]}
        return 404, None

    settings = Settings(github_token="test-token")
    enriched = enrich_release_evidence(evidence, submit, settings, http_get=fake_get)
    assert enriched.trivy.scan_status == ScanStatus.clean
    assert "trivy" not in enriched.missing_sources
    assert enriched.github.status == SourceStatus.success
    assert "github" not in enriched.missing_sources
    assert enriched.github_actions.ci_status == SourceStatus.success
    assert "github_actions" not in enriched.missing_sources


def test_failed_github_fetch_is_failed_not_invented() -> None:
    submit = ReleaseEvidenceSubmit(
        release_id="REL-011",
        repository="owner/repo",
        commit_sha="abc123def456",
        ci_status=SourceStatus.success,
        test_status=SourceStatus.success,
        critical_vulnerabilities=0,
        high_vulnerabilities=0,
    )
    evidence = expand_release_evidence(submit)
    settings = Settings(github_token="test-token")

    def fake_get(_url: str):
        return 401, None

    enriched = enrich_release_evidence(evidence, submit, settings, http_get=fake_get)
    assert enriched.github.status == SourceStatus.unknown
    assert enriched.github.changed_files_count is None
    assert "github" in enriched.failed_sources
    assert "github" in enriched.missing_sources
