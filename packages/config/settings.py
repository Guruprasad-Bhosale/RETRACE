"""Application Configuration Module using Pydantic Settings.

Provides environment-aware configuration with strict production validation rules,
worker resource boundaries, and secure secret handling.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-driven loading and production validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    ENVIRONMENT: Literal["development", "test", "testing", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"
    SERVICE_NAME: str = "retrace-api"
    SECRET_KEY: str = Field(
        default="retrace-dev-secret-key-change-in-production",
        description="Master secret key for cryptographically secure operations",
    )

    # API Security & Networking
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
    ]
    ENABLE_SECURITY_HEADERS: bool = True

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
    DATABASE_AUTO_MIGRATE: bool = False

    # Redis / Stream Processing
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STREAM_KEY: str = "retrace:analysis:jobs"
    REDIS_CONSUMER_GROUP: str = "retrace-worker-group"
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_JOB_TIMEOUT_S: int = 900
    REDIS_MAX_DELIVERY_ATTEMPTS: int = 3

    # Artifact Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = "./storage_data/artifacts"

    # S3 / MinIO Settings
    STORAGE_S3_ENDPOINT_URL: str | None = None
    STORAGE_S3_BUCKET: str = "retrace-artifacts"
    STORAGE_S3_ACCESS_KEY: str | None = None
    STORAGE_S3_SECRET_KEY: str | None = None
    STORAGE_S3_REGION: str = "us-east-1"
    STORAGE_S3_USE_SSL: bool = True
    STORAGE_S3_PREFIX: str = "artifacts"

    # Worker Resource Budgets & Sandbox Limits
    WORKER_CONCURRENCY: int = 4
    WORKER_MAX_MEMORY_MB: int = 2048
    WORKER_MAX_EXECUTION_TIME_S: int = 600
    WORKER_MAX_BROWSER_PAGES: int = 50
    WORKER_MAX_EXPLORATION_STATES: int = 100
    WORKER_MAX_ARTIFACT_SIZE_MB: int = 100
    WORKER_BROWSER_SANDBOX: bool = True
    WORKER_ALLOW_EXTERNAL_NETWORK: bool = False
    WORKER_BLOCKED_HOSTS: list[str] = [
        "169.254.169.254",  # AWS IMDSv1/v2
        "metadata.google.internal",
        "100.100.100.200",  # Alibaba metadata
    ]

    # AI Provider (Strictly Non-Authoritative)
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    LLM_ENABLED: bool = False

    @model_validator(mode="after")
    def validate_production_guards(self) -> "Settings":
        """Strict production configuration validator ensuring zero default insecure settings."""
        if self.ENVIRONMENT == "production":
            errors: list[str] = []

            if self.DEBUG:
                errors.append("DEBUG mode must be False in production.")

            if "retrace-dev-secret-key" in self.SECRET_KEY:
                errors.append("SECRET_KEY must be overridden with a secure random secret in production.")

            if "localhost" in self.DATABASE_URL or "postgres:postgres@" in self.DATABASE_URL:
                errors.append("DATABASE_URL must not point to localhost or use default credentials in production.")

            if "localhost" in self.REDIS_URL:
                errors.append("REDIS_URL must not point to localhost in production.")

            if self.STORAGE_BACKEND == "local":
                errors.append("STORAGE_BACKEND must be 's3' in production.")

            if "*" in self.CORS_ORIGINS:
                errors.append("CORS_ORIGINS must not contain wildcard '*' in production.")

            if errors:
                raise ValueError(
                    f"Production configuration validation failed with {len(errors)} error(s):\n - "
                    + "\n - ".join(errors)
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
