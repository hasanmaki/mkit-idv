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

from pydantic_settings import BaseSettings


class CorsConfig(BaseSettings):
    """CORS configuration settings."""

    model_config = {"env_prefix": "CORS_"}

    allow_origins: list[str] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = True


class JwtConfig(BaseSettings):
    """JWT configuration settings."""

    model_config = {"env_prefix": "JWT_"}

    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 300  # 5 hours
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    model_config = {"env_prefix": "DB_"}

    db_url: str = "sqlite+aiosqlite:///./application.db"


class LogConfig(BaseSettings):
    """Logging configuration settings."""

    model_config = {"env_prefix": "LOG_"}

    # Base configuration
    log_level: str = "INFO"  # Can be overridden via env
    log_file: str = "logs/app.log"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    # Advanced options
    log_format: str | None = None  # Custom format (optional)
    log_json: bool = False  # JSON format for production
    log_colorize: bool = True  # Colorize terminal output
    log_backtrace: bool = False  # Enable backtrace for errors
    log_diagnose: bool = False  # Enable diagnose for errors


class AppSettings(BaseSettings):
    """Application settings for FastAPI app."""

    app_name: str = "mkit-indosat voucher service"
    app_version: str = "0.1.0"
    debug: bool = False
    db: str = DatabaseConfig().db_url
    cors: CorsConfig = CorsConfig()
    jwt: JwtConfig = JwtConfig()
    log: LogConfig = LogConfig()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_nested_delimiter": "__",
    }


@lru_cache
def get_app_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()
