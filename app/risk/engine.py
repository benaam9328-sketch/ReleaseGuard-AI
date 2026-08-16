from app.risk.catalog import (
    DORA_TREND_WINDOW_DAYS,
    DORA_WINDOW_DAYS,
    LOW_MAX,
    MEDIUM_MAX,
    SCORE_CAP,
)
from app.risk.detectors import collect_signals
from app.schemas.assessment import (
    Assessment,
    DoraContext,
    EvidenceSummary,
    RiskSignal,
)
from app.schemas.enums import Recommendation, RiskLevel
from app.schemas.evidence import ReleaseEvidence


def dedupe_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    best: dict[str, RiskSignal] = {}
    for signal in signals:
        group = signal.deduplication_group.value
        current = best.get(group)
        if current is None or signal.weight > current.weight:
            best[group] = signal
    return list(best.values())


def score_signals(signals: list[RiskSignal]) -> int:
    return min(SCORE_CAP, sum(signal.weight for signal in signals))


def band_for_score(score: int) -> tuple[RiskLevel, Recommendation]:
    if score <= LOW_MAX:
        return RiskLevel.LOW, Recommendation.ALLOW
    if score <= MEDIUM_MAX:
        return RiskLevel.MEDIUM, Recommendation.REQUIRE_HUMAN_REVIEW
    return RiskLevel.HIGH, Recommendation.BLOCK_APPROVAL_REQUIRED


def _history_summary(evidence: ReleaseEvidence) -> str:
    if evidence.history.similar_historical_failure is True:
        return "similar_failure"
    if evidence.history.status.value == "unknown":
        return "unknown"
    return "none"


def assess(evidence: ReleaseEvidence) -> Assessment:
    fired = collect_signals(evidence)
    applicable = dedupe_signals(fired)
    risk_score = score_signals(applicable)
    risk_level, recommendation = band_for_score(risk_score)
    return Assessment(
        release_id=evidence.release_id,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        enforcement="none",
        signals=applicable,
        evidence_summary=EvidenceSummary(
            ci_status=evidence.github_actions.ci_status,
            test_status=evidence.github_actions.test_status,
            trivy=evidence.trivy.scan_status.value,
            history=_history_summary(evidence),
        ),
        dora_context=DoraContext(
            window_days=DORA_WINDOW_DAYS,
            trend_window_days=DORA_TREND_WINDOW_DAYS,
        ),
    )
