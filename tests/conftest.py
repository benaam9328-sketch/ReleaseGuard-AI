import os

os.environ.pop("DATABASE_URL", None)

from app.storage import store


def pytest_configure() -> None:
    store.reset_memory()
    store.backend = "memory"
    store._session_factory = None
