"""Application configuration loading for environment variables and .env settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    database_url: str = "postgresql+asyncpg://skillet:change-me@postgres:5432/skillet"
    secret_key: str = "change-me"
    cookie_name: str = "skillet-session"
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
