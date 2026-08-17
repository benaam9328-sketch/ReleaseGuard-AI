from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.releases import _complete_assessment
from app.config import get_settings
from app.demo.seed import seed_demo_release
from app.schemas.assessment import ReleaseAnalyzeResponse
from app.storage import EvidenceStore, get_store

router = APIRouter(prefix="/v1/demo", tags=["demo"])


class DemoSeedRequest(BaseModel):
    release_id: str = "REL-001"


@router.post("/seed", response_model=ReleaseAnalyzeResponse, status_code=status.HTTP_201_CREATED)
def seed_demo(
    payload: DemoSeedRequest,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> ReleaseAnalyzeResponse:
    evidence = seed_demo_release(store, get_settings(), payload.release_id)
    assessment = _complete_assessment(evidence, store)
    return ReleaseAnalyzeResponse(evidence=evidence, assessment=assessment)
