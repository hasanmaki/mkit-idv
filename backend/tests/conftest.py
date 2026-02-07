import contextlib
import os

import pytest
from app.core.settings import get_app_settings


@pytest.fixture
def clear_env_vars(monkeypatch):
    """Clear environment variables that may affect AppSettings during tests.

    This removes variables commonly set by the `.env` we generate and any
    prefixed variables (DB_, JWT_, CORS_, LOG_, APP_). It also clears the
    cached `get_app_settings` so tests get fresh settings.
    """
    keys_to_remove = [
        "APP_NAME",
        "APP_VERSION",
        "DEBUG",
    ]
    # remove envs with these prefixes
    prefixes = ("DB_", "JWT_", "CORS_", "LOG_")

    for k in list(os.environ.keys()):
        if k in keys_to_remove or k.startswith(prefixes):
            monkeypatch.delenv(k, raising=False)

    # clear cached settings and ensure tests have a deterministic JWT secret

    with contextlib.suppress(AttributeError):
        get_app_settings.cache_clear()

    # provide a test-only JWT secret so tests don't rely on local .env
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")

    yield

    # ensure cache cleared after test as well
    with contextlib.suppress(AttributeError):
        get_app_settings.cache_clear()
    # cleanup test JWT secret
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
