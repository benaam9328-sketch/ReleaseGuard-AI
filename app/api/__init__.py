from fastapi import APIRouter

from app.api.dora import router as dora_router
from app.api.health import router as health_router
from app.api.releases import router as releases_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(releases_router)
api_router.include_router(dora_router)
