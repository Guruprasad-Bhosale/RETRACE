"""Application Configuration Module using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SERVICE_NAME: str = "retrace-api"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/retrace_dev",
        description="Async connection URL for SQLAlchemy (asyncpg)",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/retrace_dev",
        description="Sync connection URL for Alembic migrations",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STREAM_KEY: str = "retrace:analysis:jobs"
    REDIS_CONSUMER_GROUP: str = "retrace-worker-group"

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = "./storage_data/artifacts"

    # S3 / MinIO Settings
    STORAGE_S3_ENDPOINT_URL: str | None = "http://localhost:9000"
    STORAGE_S3_BUCKET: str = "retrace-artifacts"
    STORAGE_S3_ACCESS_KEY: str = "minioadmin"
    STORAGE_S3_SECRET_KEY: str = "minioadmin"
    STORAGE_S3_REGION: str = "us-east-1"
    STORAGE_S3_USE_SSL: bool = False

    # AI Provider
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
