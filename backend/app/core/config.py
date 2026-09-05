"""Application configuration loading for environment variables and .env settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    database_url: str = "postgresql+asyncpg://skillet:change-me@postgres:5432/skillet"
    secret_key: str = "change-me"
    cookie_name: str = "skillet-session"
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    login_rate_limit: str = "5/minute"
    upload_dir: str = "./uploads"
    max_upload_size: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
