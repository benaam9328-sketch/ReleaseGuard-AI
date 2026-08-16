import os

os.environ.pop("DATABASE_URL", None)
# Empty strings override .env so tests never call live GitHub or Groq.
os.environ["GITHUB_TOKEN"] = ""
os.environ["GITHUB_REPOSITORY"] = ""
os.environ["GROQ_API_KEY"] = ""

from app.storage import store


def pytest_configure():
    store.reset_memory()
    store.backend = "memory"
    store._session_factory = None
