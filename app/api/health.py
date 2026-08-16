from fastapi import APIRouter, HTTPException

from app.storage import get_store

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "releaseguard-ai"}


@router.get("/ready")
def ready() -> dict[str, str]:
    evidence_store = get_store()
    if evidence_store.backend == "postgres":
        try:
            evidence_store.get("__readiness_probe__")
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="postgres_unavailable",
            ) from exc
    return {"status": "ok", "storage": evidence_store.backend}
