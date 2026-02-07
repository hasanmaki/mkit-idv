# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Module Title.

Short description of this module and its responsibilities. Explain its purpose within the application architecture.

Key Features:
    - First key feature
    - Second key feature

Attributes:
    - Second key feature
    - Second key feature

Example:
    from module import something

Note:
    - Important constraints or considerations
"""

# services/auth/session_errors.py

from app.core.exceptions import AppBaseExceptionError


class SessionError(AppBaseExceptionError):
    """Base class for session-related errors."""

    DEFAULT_MESSAGE = "Terjadi kesalahan pada sesi."
    DEFAULT_STATUS_CODE = 401
    DEFAULT_CODE = "session_error"


class SessionNotFoundError(SessionError):
    """Session not found or does not exist."""

    DEFAULT_MESSAGE = "Sesi tidak ditemukan."
    DEFAULT_CODE = "session_not_found"


class SessionRevokedError(SessionError):
    """Session has been revoked (force logout)."""

    DEFAULT_MESSAGE = "Sesi telah dicabut. Silakan login ulang."
    DEFAULT_CODE = "session_revoked"


class SessionExpiredError(SessionError):
    """Session expired in database."""

    DEFAULT_MESSAGE = "Sesi telah kedaluwarsa."
    DEFAULT_CODE = "session_expired"


class RefreshTokenMismatchError(SessionError):
    """Refresh token hash does not match."""

    DEFAULT_MESSAGE = "Refresh token tidak valid."
    DEFAULT_CODE = "refresh_token_mismatch"
