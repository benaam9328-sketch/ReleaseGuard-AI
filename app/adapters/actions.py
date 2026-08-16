from datetime import datetime

from app.schemas.enums import SourceName, SourceStatus
from app.schemas.evidence import GithubActionsEvidence

_CONCLUSION_MAP = {
    "success": SourceStatus.success,
    "failure": SourceStatus.failure,
    "timed_out": SourceStatus.failure,
    "cancelled": SourceStatus.failure,
    "startup_failure": SourceStatus.failure,
}


def _map_conclusion(value: str | None) -> SourceStatus:
    if not value:
        return SourceStatus.unknown
    return _CONCLUSION_MAP.get(value, SourceStatus.unknown)


def _duration_seconds(run: dict) -> int | None:
    start = run.get("run_started_at") or run.get("created_at")
    end = run.get("updated_at")
    if not start or not end:
        return None
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    delta = int((end_dt - start_dt).total_seconds())
    if delta < 0:
        return None
    return delta


def actions_evidence_from_runs(
    runs_payload: dict,
    jobs_payload: dict | None = None,
) -> GithubActionsEvidence:
    runs = runs_payload.get("workflow_runs") or []
    if not runs:
        return GithubActionsEvidence(
            status=SourceStatus.unknown,
            source=SourceName.github_actions,
            ci_status=SourceStatus.unknown,
            test_status=SourceStatus.unknown,
            deployment_workflow_status=SourceStatus.unknown,
        )

    run = runs[0]
    ci_status = _map_conclusion(run.get("conclusion"))
    test_status = ci_status
    jobs = []
    if jobs_payload:
        jobs = jobs_payload.get("jobs") or []
    for job in jobs:
        name = str(job.get("name") or "").lower()
        if "test" in name:
            test_status = _map_conclusion(job.get("conclusion"))
            break

    deploy_status = SourceStatus.unknown
    workflow_name = run.get("name")
    if workflow_name and "deploy" in str(workflow_name).lower():
        deploy_status = ci_status

    return GithubActionsEvidence(
        status=ci_status,
        source=SourceName.github_actions,
        ci_status=ci_status,
        test_status=test_status,
        workflow_name=workflow_name,
        workflow_run_id=str(run["id"]) if run.get("id") is not None else None,
        workflow_duration_seconds=_duration_seconds(run),
        deployment_workflow_status=deploy_status,
    )
