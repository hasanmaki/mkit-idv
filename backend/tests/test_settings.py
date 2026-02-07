"""test the get app settings function."""

import contextlib

from app.core.settings import get_app_settings


def test_get_app_settings(monkeypatch) -> None:
    """Test get_app_settings function."""
    # Ensure a deterministic JWT secret for the test
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
    import os

    assert os.environ.get("JWT_SECRET_KEY") == "test-jwt-secret"
    with contextlib.suppress(Exception):
        get_app_settings.cache_clear()

    settings = get_app_settings()
    assert settings.app_name == "mkit-indosat voucher service"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.db == "sqlite+aiosqlite:///./application.db"
    assert settings.cors.allow_origins == ["*"]
    assert settings.jwt.secret == "test-jwt-secret"


def test_get_app_settings_cached() -> None:
    """Test that get_app_settings function is cached."""
    settings1 = get_app_settings()
    settings2 = get_app_settings()
    assert settings1 is settings2
