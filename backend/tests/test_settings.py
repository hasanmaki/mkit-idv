"""test the get app settings function."""

import pytest
from app.core.settings import get_app_settings


@pytest.mark.usefixtures("clear_env_vars")
def test_get_app_settings() -> None:
    """Test get_app_settings function."""
    settings = get_app_settings()
    assert settings.app_name == "mkit-indosat voucher service"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.db == "sqlite+aiosqlite:///./application.db"
    assert settings.cors.allow_origins == ["*"]


def test_get_app_settings_cached() -> None:
    """Test that get_app_settings function is cached."""
    settings1 = get_app_settings()
    settings2 = get_app_settings()
    assert settings1 is settings2
