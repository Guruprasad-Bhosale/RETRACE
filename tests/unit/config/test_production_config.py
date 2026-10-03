"""Unit tests for production configuration validation rules."""

import pytest
from pydantic import ValidationError

from packages.config.settings import Settings
from packages.config.validator import CheckStatus, ConfigurationValidator


def test_production_fails_on_debug_mode():
    """Verify production settings reject DEBUG=True."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="prod-secret-key-super-secure-32chars",
            DATABASE_URL="postgresql+asyncpg://admin:secure_pass@db.prod.internal:5432/retrace",
            DATABASE_SYNC_URL="postgresql://admin:secure_pass@db.prod.internal:5432/retrace",
            REDIS_URL="redis://redis.prod.internal:6379/0",
            STORAGE_BACKEND="s3",
            CORS_ORIGINS=["https://app.retrace.io"],
        )
    assert "DEBUG mode must be False in production" in str(exc.value)


def test_production_fails_on_default_secret_key():
    """Verify production settings reject default SECRET_KEY."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="retrace-dev-secret-key-change-in-production",
            DATABASE_URL="postgresql+asyncpg://admin:secure_pass@db.prod.internal:5432/retrace",
            DATABASE_SYNC_URL="postgresql://admin:secure_pass@db.prod.internal:5432/retrace",
            REDIS_URL="redis://redis.prod.internal:6379/0",
            STORAGE_BACKEND="s3",
            CORS_ORIGINS=["https://app.retrace.io"],
        )
    assert "SECRET_KEY must be overridden" in str(exc.value)


def test_production_fails_on_local_storage():
    """Verify production settings reject STORAGE_BACKEND='local'."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="prod-secret-key-super-secure-32chars",
            DATABASE_URL="postgresql+asyncpg://admin:secure_pass@db.prod.internal:5432/retrace",
            DATABASE_SYNC_URL="postgresql://admin:secure_pass@db.prod.internal:5432/retrace",
            REDIS_URL="redis://redis.prod.internal:6379/0",
            STORAGE_BACKEND="local",
            CORS_ORIGINS=["https://app.retrace.io"],
        )
    assert "STORAGE_BACKEND must be 's3' in production" in str(exc.value)


def test_production_valid_configuration_passes():
    """Verify valid production settings pass validation without error."""
    cfg = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="prod-secret-key-super-secure-32chars",
        DATABASE_URL="postgresql+asyncpg://admin:secure_pass@db.prod.internal:5432/retrace",
        DATABASE_SYNC_URL="postgresql://admin:secure_pass@db.prod.internal:5432/retrace",
        REDIS_URL="redis://redis.prod.internal:6379/0",
        STORAGE_BACKEND="s3",
        STORAGE_S3_BUCKET="retrace-prod-artifacts",
        CORS_ORIGINS=["https://app.retrace.io"],
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.DEBUG is False

    results = ConfigurationValidator.audit(cfg)
    failures = [r for r in results if r.status == CheckStatus.FAIL]
    assert len(failures) == 0


def test_production_preflight_validator_structure():
    """Verify ProductionPreflightValidator returns structured report without leaking secrets."""
    from packages.config.preflight import PreflightStatus, ProductionPreflightValidator

    validator = ProductionPreflightValidator()
    report = validator.run_all_checks()

    assert report.overall_status in (PreflightStatus.PASS, PreflightStatus.BLOCKED, PreflightStatus.FAIL)
    assert len(report.results) >= 13

    # Ensure no secret strings appear in results or report dict
    report_dict = report.to_dict()
    report_str = str(report_dict)
    assert "retrace-dev-secret-key" not in report_str
    assert "AWS_SECRET_ACCESS_KEY" not in report_str

