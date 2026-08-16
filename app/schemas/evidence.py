from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import ScanStatus, SourceName, SourceStatus

CRITICAL_SOURCES = (
    SourceName.github.value,
    SourceName.github_actions.value,
    SourceName.trivy.value,
)


class ChangedFile(BaseModel):
    path: str
    change_type: str


class GithubEvidence(BaseModel):
    status: SourceStatus
    source: SourceName = SourceName.github
    pull_request_number: int | None = None
    first_commit_sha: str | None = None
    first_commit_at: datetime | None = None
    head_commit_sha: str | None = None
    head_commit_at: datetime | None = None
    authors: list[str] | None = None
    changed_files_count: int | None = None
    lines_changed: int | None = None
    changed_files: list[ChangedFile] | None = None
    database_migration_detected: bool | None = None

    @model_validator(mode="after")
    def require_fields_when_success(self) -> "GithubEvidence":
        if self.status != SourceStatus.success:
            return self
        required = {
            "first_commit_sha": self.first_commit_sha,
            "first_commit_at": self.first_commit_at,
            "head_commit_sha": self.head_commit_sha,
            "head_commit_at": self.head_commit_at,
            "changed_files_count": self.changed_files_count,
            "database_migration_detected": self.database_migration_detected,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise ValueError(
                f"github.status=success requires fields: {', '.join(missing)}"
            )
        return self


class GithubActionsEvidence(BaseModel):
    status: SourceStatus
    source: SourceName = SourceName.github_actions
    ci_status: SourceStatus | None = None
    test_status: SourceStatus | None = None
    workflow_name: str | None = None
    workflow_run_id: str | None = None
    workflow_duration_seconds: int | None = None
    deployment_workflow_status: SourceStatus | None = SourceStatus.unknown

    @model_validator(mode="after")
    def require_fields_when_success(self) -> "GithubActionsEvidence":
        if self.status != SourceStatus.success:
            return self
        if self.ci_status is None or self.test_status is None:
            raise ValueError(
                "github_actions.status=success requires ci_status and test_status"
            )
        return self


class TrivyFinding(BaseModel):
    vulnerability_id: str
    severity: str
    package: str | None = None
    title: str | None = None


class TrivyEvidence(BaseModel):
    status: SourceStatus
    source: SourceName = SourceName.trivy
    scan_status: ScanStatus
    critical: int | None = None
    high: int | None = None
    medium: int | None = None
    low: int | None = None
    findings: list[TrivyFinding] | None = None

    @model_validator(mode="after")
    def counts_when_scanned(self) -> "TrivyEvidence":
        if self.scan_status in {ScanStatus.scan_failed, ScanStatus.unavailable}:
            if self.critical is not None or self.high is not None:
                raise ValueError(
                    "Trivy counts must stay null when scan_status is "
                    "scan_failed or unavailable"
                )
            return self
        if self.scan_status in {ScanStatus.clean, ScanStatus.findings}:
            if self.critical is None or self.high is None:
                raise ValueError(
                    "Trivy critical and high counts are required when "
                    "scan_status is clean or findings"
                )
            if self.critical < 0 or self.high < 0:
                raise ValueError("Trivy counts must be >= 0")
            if self.medium is not None and self.medium < 0:
                raise ValueError("Trivy counts must be >= 0")
            if self.low is not None and self.low < 0:
                raise ValueError("Trivy counts must be >= 0")
        return self


class InfrastructureEvidence(BaseModel):
    status: SourceStatus = SourceStatus.unknown
    source: SourceName = SourceName.terraform
    high_risk_change_detected: bool | None = None


class HistoryEvidence(BaseModel):
    status: SourceStatus = SourceStatus.unknown
    similar_historical_failure: bool | None = None
    rollback_required_recently: bool | None = None
    is_synthetic: bool = False


class ReleaseEvidence(BaseModel):
    release_id: str
    repository: str
    commit_sha: str
    service: str
    environment: str
    created_at: datetime
    github: GithubEvidence
    github_actions: GithubActionsEvidence
    trivy: TrivyEvidence
    infrastructure: InfrastructureEvidence
    history: HistoryEvidence
    missing_sources: list[str] = Field(default_factory=list)
    failed_sources: list[str] = Field(default_factory=list)
    is_synthetic: bool = False

    @model_validator(mode="after")
    def head_commit_matches_release(self) -> "ReleaseEvidence":
        head = self.github.head_commit_sha
        if (
            self.github.status == SourceStatus.success
            and head is not None
            and head != self.commit_sha
        ):
            raise ValueError("github.head_commit_sha must match commit_sha")
        return self


class ReleaseEvidenceSubmit(BaseModel):
    """Accepts compact first-slice input or a partial/canonical evidence object."""

    release_id: str
    repository: str
    commit_sha: str
    service: str | None = None
    environment: str | None = None
    created_at: datetime | None = None
    is_synthetic: bool = False
    ci_status: SourceStatus | None = None
    test_status: SourceStatus | None = None
    critical_vulnerabilities: int | None = Field(default=None, ge=0)
    high_vulnerabilities: int | None = Field(default=None, ge=0)
    medium_vulnerabilities: int | None = Field(default=None, ge=0)
    low_vulnerabilities: int | None = Field(default=None, ge=0)
    github: GithubEvidence | None = None
    github_actions: GithubActionsEvidence | None = None
    trivy: TrivyEvidence | None = None
    infrastructure: InfrastructureEvidence | None = None
    history: HistoryEvidence | None = None
    missing_sources: list[str] = Field(default_factory=list)
    failed_sources: list[str] = Field(default_factory=list)
