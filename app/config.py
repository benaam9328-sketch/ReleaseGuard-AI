from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ReleaseGuard AI"
    database_url: str | None = None


def get_settings() -> Settings:
    return Settings()
