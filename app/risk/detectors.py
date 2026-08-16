from app.risk.catalog import (
    CATALOG,
    CRITICAL_SOURCE_NAMES,
    LARGE_CHANGE_FILES,
    LARGE_CHANGE_LINES,
)
from app.schemas.assessment import RiskSignal
from app.schemas.enums import ScanStatus, SignalId, SourceName, SourceStatus
from app.schemas.evidence import ReleaseEvidence


def _signal(signal_id: SignalId, evidence: str, source: SourceName) -> RiskSignal:
    spec = CATALOG[signal_id]
    return RiskSignal(
        signal=spec.signal,
        severity=spec.severity,
        weight=spec.weight,
        evidence=evidence,
        source=source,
        deduplication_group=spec.group,
    )


def _is_migration_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    if "/migrations/" in normalized or normalized.startswith("migrations/"):
        return True
    if "/alembic/versions/" in normalized:
        return True
    filename = normalized.rsplit("/", 1)[-1]
    return "migration" in filename


def collect_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    signals: list[RiskSignal] = []
    signals.extend(_ci_signals(evidence))
    signals.extend(_trivy_signals(evidence))
    signals.extend(_change_signals(evidence))
    signals.extend(_infra_signals(evidence))
    signals.extend(_history_signals(evidence))
    signals.extend(_missing_evidence_signals(evidence))
    return signals


def _ci_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    actions = evidence.github_actions
    if actions.ci_status == SourceStatus.failure:
        return [
            _signal(
                SignalId.ci_failure,
                f"CI status is {actions.ci_status.value}",
                SourceName.github_actions,
            )
        ]
    if actions.test_status == SourceStatus.failure:
        return [
            _signal(
                SignalId.ci_failure,
                f"Test status is {actions.test_status.value}",
                SourceName.github_actions,
            )
        ]
    return []


def _trivy_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    trivy = evidence.trivy
    if trivy.scan_status in {ScanStatus.scan_failed, ScanStatus.unavailable}:
        return []
    signals: list[RiskSignal] = []
    if trivy.critical is not None and trivy.critical >= 1:
        finding = _first_finding(evidence, "CRITICAL")
        signals.append(
            _signal(
                SignalId.critical_vulnerability,
                finding or f"Trivy critical count is {trivy.critical}",
                SourceName.trivy,
            )
        )
    if trivy.high is not None and trivy.high >= 1:
        finding = _first_finding(evidence, "HIGH")
        signals.append(
            _signal(
                SignalId.high_vulnerability,
                finding or f"Trivy high count is {trivy.high}",
                SourceName.trivy,
            )
        )
    return signals


def _first_finding(evidence: ReleaseEvidence, severity: str) -> str | None:
    findings = evidence.trivy.findings or []
    for finding in findings:
        if finding.severity.upper() == severity:
            return f"Trivy finding {finding.vulnerability_id}"
    return None


def _change_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    github = evidence.github
    signals: list[RiskSignal] = []
    migration = github.database_migration_detected is True
    if github.changed_files:
        migration = migration or any(
            _is_migration_path(item.path) for item in github.changed_files
        )
    if migration:
        signals.append(
            _signal(
                SignalId.database_migration,
                "Database migration detected in changed files",
                SourceName.github,
            )
        )
    files = github.changed_files_count
    lines = github.lines_changed
    large = (files is not None and files >= LARGE_CHANGE_FILES) or (
        lines is not None and lines >= LARGE_CHANGE_LINES
    )
    if large:
        signals.append(
            _signal(
                SignalId.large_change_surface,
                f"Change surface files={files} lines={lines}",
                SourceName.github,
            )
        )
    return signals


def _infra_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    if evidence.infrastructure.high_risk_change_detected is True:
        return [
            _signal(
                SignalId.high_risk_infrastructure_change,
                "Infrastructure adapter reported a high-risk change",
                SourceName.terraform,
            )
        ]
    return []


def _history_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    history = evidence.history
    signals: list[RiskSignal] = []
    if history.rollback_required_recently is True:
        signals.append(
            _signal(
                SignalId.rollback_required,
                "Rollback required for this release or similar change",
                SourceName.history,
            )
        )
    if history.similar_historical_failure is True:
        signals.append(
            _signal(
                SignalId.similar_historical_failure,
                "Similar historical failure matched",
                SourceName.history,
            )
        )
    return signals


def _missing_evidence_signals(evidence: ReleaseEvidence) -> list[RiskSignal]:
    named = set(evidence.missing_sources) | set(evidence.failed_sources)
    if evidence.trivy.scan_status in {ScanStatus.scan_failed, ScanStatus.unavailable}:
        named.add(SourceName.trivy.value)
    missing_critical = [name for name in CRITICAL_SOURCE_NAMES if name in named]
    if not missing_critical:
        return []
    return [
        _signal(
            SignalId.missing_critical_evidence,
            "Missing or failed critical sources: " + ", ".join(missing_critical),
            SourceName.github,
        )
    ]
