# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Application Settings.

we use pydantic-settings to manage application settings and configurations.
Key Features:


Attributes:
    - Second key feature
    - Second key feature

Example:
    from module import something

Note:
    - Important constraints or considerations
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class CorsConfig(BaseSettings):
    """CORS configuration settings."""

    model_config = {"env_prefix": "CORS_"}

    allow_origins: list[str] = ["http://localhost", "https://yourdomain.com"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = True


class HttpxConfig(BaseSettings):
    """HTTPX client configuration settings."""

    model_config = {"env_prefix": "HTTPX_"}

    timeout_seconds: float = 10.0
    max_connections: int = 100
    max_keepalive: int = 20
    retries: int = 3
    backoff_factor: float = 0.2


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration settings."""

    model_config = {"env_prefix": "RATE_LIMIT_"}

    enabled: bool = True
    provider: str = "fastapi-limiter"
    default_limits: list[str] = []
    storage_uri: str | None = None
    headers_enabled: bool = True


class JwtConfig(BaseSettings):
    """JWT configuration settings."""

    model_config = {"env_prefix": "JWT_"}

    # Do NOT hardcode secrets. Use SecretStr and require env in production.
    secret_key: SecretStr | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @property
    def secret(self) -> str:
        """Return the raw secret string or raise if missing.

        This enforces that callers actively choose what to do when secret is
        missing (e.g. fail fast in production) instead of silently using a
        hardcoded value.
        """
        if self.secret_key is None:
            raise RuntimeError("JWT secret (JWT_SECRET_KEY) is not configured")
        return self.secret_key.get_secret_value()


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    model_config = {"env_prefix": "DB_"}

    db_url: str = "sqlite+aiosqlite:///./application.db"


class AdminConfig(BaseSettings):
    """Default admin credentials for seeding."""

    model_config = {"env_prefix": "ADMIN_"}

    name: str
    username: str
    email: str
    password: SecretStr


class AppSettings(BaseSettings):
    """Application settings for FastAPI app."""

    app_name: str = "mkit-indosat voucher service"
    app_version: str = "0.1.0"
    debug: bool = False
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    jwt: JwtConfig = Field(default_factory=JwtConfig)
    httpx: HttpxConfig = Field(default_factory=HttpxConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    admin: AdminConfig

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }


@lru_cache
def get_app_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()  # type: ignore
