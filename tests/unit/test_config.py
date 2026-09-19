"""Unit tests for configuration loading."""

from packages.config.settings import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.API_PORT == 8000
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.REDIS_STREAM_KEY == "retrace:analysis:jobs"
    assert settings.STORAGE_BACKEND in ("local", "s3")


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("API_PORT", "9090")
    settings = Settings()
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.API_PORT == 9090
