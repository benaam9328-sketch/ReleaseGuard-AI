from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.enrich import enrich_release_evidence
from app.config import get_settings
from app.normalize import expand_release_evidence
from app.risk.engine import assess
from app.schemas.assessment import (
    Approval,
    ApprovalRequest,
    Assessment,
    ReleaseAnalyzeResponse,
)
from app.schemas.enums import ApprovalDecision, ApprovalState
from app.schemas.evidence import ReleaseEvidence, ReleaseEvidenceSubmit
from app.storage import EvidenceStore, get_store

router = APIRouter(prefix="/v1", tags=["releases"])


def _with_stored_approval(assessment: Assessment, store: EvidenceStore) -> Assessment:
    stored = store.get_approval(assessment.release_id)
    if stored is not None:
        assessment.approval = stored
    return assessment


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
    saved, _created = store.save(evidence)
    assessment = _with_stored_approval(assess(saved), store)
    return ReleaseAnalyzeResponse(evidence=saved, assessment=assessment)


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
    return _with_stored_approval(assess(evidence), store)


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

    assessment = assess(evidence)
    assessment.approval = approval
    return assessment
