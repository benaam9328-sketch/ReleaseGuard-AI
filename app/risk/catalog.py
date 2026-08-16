from dataclasses import dataclass

from app.schemas.enums import DedupGroup, SignalId, SignalSeverity

SCORE_CAP = 100
LOW_MAX = 30
MEDIUM_MAX = 60
LARGE_CHANGE_FILES = 20
LARGE_CHANGE_LINES = 500
DORA_WINDOW_DAYS = 30
DORA_TREND_WINDOW_DAYS = 7
CRITICAL_SOURCE_NAMES = ("github", "github_actions", "trivy")


@dataclass(frozen=True)
class SignalSpec:
    signal: SignalId
    severity: SignalSeverity
    weight: int
    group: DedupGroup


CATALOG: dict[SignalId, SignalSpec] = {
    SignalId.ci_failure: SignalSpec(
        SignalId.ci_failure, SignalSeverity.high, 30, DedupGroup.delivery_failure
    ),
    SignalId.critical_vulnerability: SignalSpec(
        SignalId.critical_vulnerability,
        SignalSeverity.critical,
        30,
        DedupGroup.security_critical,
    ),
    SignalId.high_vulnerability: SignalSpec(
        SignalId.high_vulnerability, SignalSeverity.high, 15, DedupGroup.security_high
    ),
    SignalId.database_migration: SignalSpec(
        SignalId.database_migration, SignalSeverity.medium, 15, DedupGroup.schema_change
    ),
    SignalId.high_risk_infrastructure_change: SignalSpec(
        SignalId.high_risk_infrastructure_change,
        SignalSeverity.high,
        15,
        DedupGroup.infra_change,
    ),
    SignalId.rollback_required: SignalSpec(
        SignalId.rollback_required,
        SignalSeverity.high,
        30,
        DedupGroup.delivery_failure,
    ),
    SignalId.similar_historical_failure: SignalSpec(
        SignalId.similar_historical_failure,
        SignalSeverity.high,
        20,
        DedupGroup.historical_similarity,
    ),
    SignalId.large_change_surface: SignalSpec(
        SignalId.large_change_surface, SignalSeverity.low, 10, DedupGroup.change_surface
    ),
    SignalId.missing_critical_evidence: SignalSpec(
        SignalId.missing_critical_evidence,
        SignalSeverity.medium,
        10,
        DedupGroup.evidence_completeness,
    ),
}
