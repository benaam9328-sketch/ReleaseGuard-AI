import httpx

from app.adapters.actions import actions_evidence_from_runs
from app.adapters.github import github_evidence_from_commit
from app.adapters.trivy import parse_trivy_report
from app.config import Settings
from app.schemas.enums import ScanStatus, SourceName, SourceStatus
from app.schemas.evidence import ReleaseEvidence, ReleaseEvidenceSubmit

GITHUB_API = "https://api.github.com"


def _drop_source(names: list[str], source: str) -> None:
    if source in names:
        names.remove(source)


def _owner_repo(evidence: ReleaseEvidence, settings: Settings) -> tuple[str, str] | None:
    configured = settings.github_repository or evidence.repository
    if configured and "/" in configured:
        owner, repo = configured.split("/", 1)
        if owner and repo:
            return owner, repo
    return None


def github_get_json(url: str, token: str) -> tuple[int, dict | list | None]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=headers)
        if response.status_code >= 400:
            return response.status_code, None
        return response.status_code, response.json()


def apply_trivy_report(evidence: ReleaseEvidence, report: dict | None) -> ReleaseEvidence:
    if report is None:
        return evidence
    trivy = parse_trivy_report(report)
    evidence.trivy = trivy
    _drop_source(evidence.missing_sources, SourceName.trivy.value)
    _drop_source(evidence.failed_sources, SourceName.trivy.value)
    if trivy.scan_status in {ScanStatus.unavailable, ScanStatus.scan_failed}:
        evidence.missing_sources.append(SourceName.trivy.value)
    if trivy.scan_status == ScanStatus.scan_failed:
        evidence.failed_sources.append(SourceName.trivy.value)
    return evidence


def apply_github_adapters(
    evidence: ReleaseEvidence,
    settings: Settings,
    http_get=None,
) -> ReleaseEvidence:
    if not settings.github_token:
        return evidence
    repo = _owner_repo(evidence, settings)
    if repo is None:
        return evidence

    token = settings.github_token

    def do_get(url: str) -> tuple[int, dict | list | None]:
        if http_get is not None:
            return http_get(url)
        return github_get_json(url, token)

    owner, name = repo
    sha = evidence.commit_sha
    base = f"{GITHUB_API}/repos/{owner}/{name}"

    if evidence.github.status != SourceStatus.success:
        status, commit_payload = do_get(f"{base}/commits/{sha}")
        if status >= 400 or not isinstance(commit_payload, dict):
            if SourceName.github.value not in evidence.failed_sources:
                evidence.failed_sources.append(SourceName.github.value)
            if SourceName.github.value not in evidence.missing_sources:
                evidence.missing_sources.append(SourceName.github.value)
        else:
            _status, pulls = do_get(f"{base}/commits/{sha}/pulls")
            pr_commits = None
            if isinstance(pulls, list) and pulls:
                number = pulls[0].get("number")
                if number is not None:
                    _status, pr_commits = do_get(f"{base}/pulls/{number}/commits")
                    if not isinstance(pr_commits, list):
                        pr_commits = None
            evidence.github = github_evidence_from_commit(
                sha,
                commit_payload,
                pulls if isinstance(pulls, list) else None,
                pr_commits,
            )
            _drop_source(evidence.missing_sources, SourceName.github.value)
            _drop_source(evidence.failed_sources, SourceName.github.value)

    if evidence.github_actions.status == SourceStatus.unknown:
        status, runs = do_get(f"{base}/actions/runs?head_sha={sha}")
        if status >= 400 or not isinstance(runs, dict):
            if SourceName.github_actions.value not in evidence.failed_sources:
                evidence.failed_sources.append(SourceName.github_actions.value)
            if SourceName.github_actions.value not in evidence.missing_sources:
                evidence.missing_sources.append(SourceName.github_actions.value)
        else:
            jobs = None
            workflow_runs = runs.get("workflow_runs") or []
            if workflow_runs and workflow_runs[0].get("id") is not None:
                _status, jobs = do_get(
                    f"{base}/actions/runs/{workflow_runs[0]['id']}/jobs"
                )
                if not isinstance(jobs, dict):
                    jobs = None
            evidence.github_actions = actions_evidence_from_runs(runs, jobs)
            if evidence.github_actions.status != SourceStatus.unknown:
                _drop_source(evidence.missing_sources, SourceName.github_actions.value)
                _drop_source(evidence.failed_sources, SourceName.github_actions.value)

    return evidence


def enrich_release_evidence(
    evidence: ReleaseEvidence,
    submit: ReleaseEvidenceSubmit,
    settings: Settings,
    http_get=None,
) -> ReleaseEvidence:
    if submit.trivy is None and submit.trivy_report is not None:
        evidence = apply_trivy_report(evidence, submit.trivy_report)
    evidence = apply_github_adapters(evidence, settings, http_get)
    return evidence
