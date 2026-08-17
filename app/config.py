from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ReleaseGuard AI"
    database_url: str | None = None
    github_token: str | None = None
    github_repository: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"


def get_settings() -> Settings:
    return Settings()
