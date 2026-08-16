from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.enrich import enrich_release_evidence
from app.ai.explain import explain_assessment
from app.config import get_settings
from app.dora.metrics import calculate_dora
from app.history.matcher import apply_history
from app.normalize import expand_release_evidence
from app.risk.catalog import DORA_TREND_WINDOW_DAYS, DORA_WINDOW_DAYS
from app.risk.engine import assess
from app.schemas.assessment import (
    Approval,
    ApprovalRequest,
    Assessment,
    DoraContext,
    ReleaseAnalyzeResponse,
)
from app.schemas.enums import ApprovalDecision, ApprovalState
from app.schemas.evidence import ReleaseEvidence, ReleaseEvidenceSubmit
from app.storage import EvidenceStore, get_store

router = APIRouter(prefix="/v1", tags=["releases"])


def _attach_saved_approval(assessment: Assessment, store: EvidenceStore) -> Assessment:
    saved = store.get_approval(assessment.release_id)
    if saved is not None:
        assessment.approval = saved
    return assessment


def _complete_assessment(
    evidence: ReleaseEvidence,
    store: EvidenceStore,
) -> Assessment:
    assessment = _attach_saved_approval(assess(evidence), store)
    snapshot = calculate_dora(store.list_events(), datetime.now(timezone.utc))
    assessment.dora_context = DoraContext(
        window_days=DORA_WINDOW_DAYS,
        trend_window_days=DORA_TREND_WINDOW_DAYS,
        snapshot=snapshot,
    )
    return explain_assessment(assessment, evidence, get_settings())


@router.post(
    "/releases",
    response_model=ReleaseAnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_release(
    payload: ReleaseEvidenceSubmit,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> ReleaseAnalyzeResponse:
    evidence = expand_release_evidence(payload)
    evidence = enrich_release_evidence(evidence, payload, get_settings())
    evidence = apply_history(evidence, payload)
    stored, _created = store.save(evidence)
    assessment = _complete_assessment(stored, store)
    return ReleaseAnalyzeResponse(evidence=stored, assessment=assessment)


@router.get("/releases", response_model=list[ReleaseEvidence])
def list_releases(
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> list[ReleaseEvidence]:
    return store.list_evidence()


@router.get("/releases/{release_id}", response_model=ReleaseEvidence)
def get_release(
    release_id: str,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> ReleaseEvidence:
    evidence = store.get(release_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return evidence


@router.get("/releases/{release_id}/assessment", response_model=Assessment)
def get_assessment(
    release_id: str,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> Assessment:
    evidence = store.get(release_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="release_not_found")
    return _complete_assessment(evidence, store)


@router.post("/releases/{release_id}/approval", response_model=Assessment)
def record_approval(
    release_id: str,
    payload: ApprovalRequest,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> Assessment:
    evidence = store.get(release_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="release_not_found")

    if payload.decision == ApprovalDecision.approve:
        state = ApprovalState.approved
    else:
        state = ApprovalState.rejected

    approval = Approval(
        state=state,
        decision=payload.decision,
        decided_at=datetime.now(timezone.utc),
    )
    store.save_approval(release_id, approval)
    return _complete_assessment(evidence, store)
