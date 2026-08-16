from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.dora import DoraSnapshot
from app.schemas.enums import (
    ApprovalDecision,
    ApprovalState,
    DedupGroup,
    Recommendation,
    RiskLevel,
    SignalId,
    SignalSeverity,
    SourceName,
    SourceStatus,
)
from app.schemas.evidence import ReleaseEvidence


class RiskSignal(BaseModel):
    signal: SignalId
    severity: SignalSeverity
    weight: int
    evidence: str
    source: SourceName
    deduplication_group: DedupGroup


class EvidenceSummary(BaseModel):
    ci_status: SourceStatus | None = None
    test_status: SourceStatus | None = None
    trivy: str | None = None
    history: str | None = None


class DoraContext(BaseModel):
    window_days: int = 30
    trend_window_days: int = 7
    snapshot: DoraSnapshot | None = None


class AiExplanation(BaseModel):
    status: SourceStatus = SourceStatus.unknown
    text: str | None = None


class Approval(BaseModel):
    state: ApprovalState = ApprovalState.pending
    decision: ApprovalDecision | None = None
    decided_at: datetime | None = None


class Assessment(BaseModel):
    release_id: str
    risk_score: int
    risk_level: RiskLevel
    recommendation: Recommendation
    enforcement: str = "none"
    signals: list[RiskSignal] = Field(default_factory=list)
    evidence_summary: EvidenceSummary
    dora_context: DoraContext = Field(default_factory=DoraContext)
    ai_explanation: AiExplanation = Field(default_factory=AiExplanation)
    approval: Approval = Field(default_factory=Approval)


class ApprovalRequest(BaseModel):
    decision: ApprovalDecision


class ReleaseAnalyzeResponse(BaseModel):
    evidence: ReleaseEvidence
    assessment: Assessment
