from datetime import datetime, timezone

from app.schemas.enums import ScanStatus, SourceName, SourceStatus
from app.schemas.evidence import (
    GithubActionsEvidence,
    GithubEvidence,
    HistoryEvidence,
    InfrastructureEvidence,
    ReleaseEvidence,
    ReleaseEvidenceSubmit,
    TrivyEvidence,
)


def _combined_status(*statuses: SourceStatus | None) -> SourceStatus:
    present = [status for status in statuses if status is not None]
    if not present:
        return SourceStatus.unknown
    if SourceStatus.failure in present:
        return SourceStatus.failure
    if SourceStatus.unknown in present:
        return SourceStatus.unknown
    return SourceStatus.success


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _unknown_github(commit_sha: str) -> GithubEvidence:
    return GithubEvidence(
        status=SourceStatus.unknown,
        source=SourceName.github,
        head_commit_sha=commit_sha,
    )


def _unknown_actions() -> GithubActionsEvidence:
    return GithubActionsEvidence(
        status=SourceStatus.unknown,
        source=SourceName.github_actions,
        ci_status=SourceStatus.unknown,
        test_status=SourceStatus.unknown,
        deployment_workflow_status=SourceStatus.unknown,
    )


def _unavailable_trivy() -> TrivyEvidence:
    return TrivyEvidence(
        status=SourceStatus.unknown,
        source=SourceName.trivy,
        scan_status=ScanStatus.unavailable,
        critical=None,
        high=None,
        medium=None,
        low=None,
    )


def _trivy_from_counts(
    critical: int | None,
    high: int | None,
    medium: int | None,
    low: int | None,
) -> TrivyEvidence:
    if critical is None or high is None:
        return _unavailable_trivy()
    total_known = critical + high + (medium or 0) + (low or 0)
    scan_status = ScanStatus.findings if total_known > 0 else ScanStatus.clean
    return TrivyEvidence(
        status=SourceStatus.success,
        source=SourceName.trivy,
        scan_status=scan_status,
        critical=critical,
        high=high,
        medium=medium,
        low=low,
    )


def _actions_from_compact(
    ci_status: SourceStatus | None,
    test_status: SourceStatus | None,
) -> GithubActionsEvidence:
    if ci_status is None and test_status is None:
        return _unknown_actions()
    ci = ci_status or SourceStatus.unknown
    test = test_status or SourceStatus.unknown
    return GithubActionsEvidence(
        status=_combined_status(ci, test),
        source=SourceName.github_actions,
        ci_status=ci,
        test_status=test,
        deployment_workflow_status=SourceStatus.unknown,
    )


def expand_release_evidence(submit: ReleaseEvidenceSubmit) -> ReleaseEvidence:
    """Expand compact or partial submit payloads into canonical ReleaseEvidence.

    Compact CI/test/Trivy fields fill a source only when that nested block is
    absent. GitHub adapter details are never invented. Omitted Trivy counts
    stay null, not zero.
    """
    created_at = submit.created_at or datetime.now(timezone.utc)
    missing = list(submit.missing_sources)
    failed = list(submit.failed_sources)

    if submit.github is not None:
        github = submit.github
    else:
        github = _unknown_github(submit.commit_sha)
        _append_unique(missing, SourceName.github.value)

    if submit.github_actions is not None:
        github_actions = submit.github_actions
    elif submit.ci_status is not None or submit.test_status is not None:
        github_actions = _actions_from_compact(submit.ci_status, submit.test_status)
        if github_actions.status == SourceStatus.unknown:
            _append_unique(missing, SourceName.github_actions.value)
    else:
        github_actions = _unknown_actions()
        _append_unique(missing, SourceName.github_actions.value)

    if submit.trivy is not None:
        trivy = submit.trivy
    elif (
        submit.critical_vulnerabilities is not None
        or submit.high_vulnerabilities is not None
    ):
        trivy = _trivy_from_counts(
            submit.critical_vulnerabilities,
            submit.high_vulnerabilities,
            submit.medium_vulnerabilities,
            submit.low_vulnerabilities,
        )
    else:
        trivy = _unavailable_trivy()

    if trivy.scan_status in {ScanStatus.unavailable, ScanStatus.scan_failed}:
        _append_unique(missing, SourceName.trivy.value)
    if trivy.scan_status == ScanStatus.scan_failed:
        _append_unique(failed, SourceName.trivy.value)

    return ReleaseEvidence(
        release_id=submit.release_id,
        repository=submit.repository,
        commit_sha=submit.commit_sha,
        service=submit.service or submit.repository,
        environment=submit.environment or "production",
        created_at=created_at,
        github=github,
        github_actions=github_actions,
        trivy=trivy,
        infrastructure=submit.infrastructure or InfrastructureEvidence(),
        history=submit.history or HistoryEvidence(),
        missing_sources=missing,
        failed_sources=failed,
        is_synthetic=submit.is_synthetic,
    )
