from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings
from app.storage import store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.database_url:
        store.configure_postgres(settings.database_url)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReleaseGuard AI",
        version="0.1.0",
        description="Release risk scoring and approval API.",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
