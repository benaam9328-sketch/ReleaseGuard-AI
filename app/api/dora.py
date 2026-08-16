from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dora.metrics import calculate_dora
from app.schemas.dora import DoraSnapshot
from app.schemas.events import DeliveryEvent
from app.storage import EvidenceStore, get_store

router = APIRouter(prefix="/v1", tags=["dora"])


@router.post("/events", response_model=DeliveryEvent, status_code=status.HTTP_201_CREATED)
def submit_event(
    payload: DeliveryEvent,
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> DeliveryEvent:
    return store.save_event(payload)


@router.get("/dora", response_model=DoraSnapshot)
def get_dora(
    store: Annotated[EvidenceStore, Depends(get_store)],
) -> DoraSnapshot:
    return calculate_dora(store.list_events(), datetime.now(timezone.utc))
