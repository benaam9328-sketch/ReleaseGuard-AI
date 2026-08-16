from datetime import datetime

from app.schemas.enums import SourceName, SourceStatus
from app.schemas.evidence import ChangedFile, GithubEvidence

_STATUS_MAP = {
    "added": "added",
    "modified": "modified",
    "removed": "deleted",
    "renamed": "renamed",
    "changed": "modified",
}


def is_migration_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    if "/migrations/" in normalized or normalized.startswith("migrations/"):
        return True
    if "/alembic/versions/" in normalized or normalized.startswith("alembic/versions/"):
        return True
    filename = normalized.rsplit("/", 1)[-1]
    return "migration" in filename


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def github_evidence_from_commit(
    commit_sha: str,
    commit_payload: dict,
    pull_payload: list | None = None,
    pr_commits: list | None = None,
) -> GithubEvidence:
    files = []
    for entry in commit_payload.get("files") or []:
        path = entry.get("filename")
        if not path:
            continue
        github_status = str(entry.get("status") or "modified")
        files.append(
            ChangedFile(
                path=path,
                change_type=_STATUS_MAP.get(github_status, "modified"),
            )
        )

    stats = commit_payload.get("stats") or {}
    additions = stats.get("additions") or 0
    deletions = stats.get("deletions") or 0
    commit_info = commit_payload.get("commit") or {}
    author = None
    author_block = commit_info.get("author") or {}
    if author_block.get("name"):
        author = author_block["name"]

    head_at = parse_iso_datetime(author_block.get("date"))
    first_sha = commit_sha
    first_at = head_at
    pr_number = None

    if pull_payload and isinstance(pull_payload, list) and pull_payload:
        pr_number = pull_payload[0].get("number")
        if pr_commits:
            first = pr_commits[0]
            first_sha = first.get("sha") or first_sha
            first_commit = first.get("commit") or {}
            first_author = first_commit.get("author") or {}
            first_at = parse_iso_datetime(first_author.get("date")) or first_at

    if first_at is None or head_at is None:
        return GithubEvidence(
            status=SourceStatus.unknown,
            source=SourceName.github,
            head_commit_sha=commit_sha,
        )

    return GithubEvidence(
        status=SourceStatus.success,
        source=SourceName.github,
        pull_request_number=pr_number,
        first_commit_sha=first_sha,
        first_commit_at=first_at,
        head_commit_sha=commit_sha,
        head_commit_at=head_at,
        authors=[author] if author else None,
        changed_files_count=len(files),
        lines_changed=additions + deletions,
        changed_files=files or None,
        database_migration_detected=any(
            is_migration_path(changed.path) for changed in files
        ),
    )
