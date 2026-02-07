# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Authentication and Authorization Errors.

This module defines custom exceptions for authentication and authorization operations.
All exceptions inherit from the base AppBaseExceptionError for consistent error handling.
"""

from app.core.exceptions import AppBaseExceptionError


class AuthError(AppBaseExceptionError):
    """Base class for authentication and authorization errors."""

    DEFAULT_MESSAGE = "Terjadi kesalahan autentikasi."
    DEFAULT_STATUS_CODE = 401
    DEFAULT_CODE = "auth_error"
    DEFAULT_LOG_LEVEL = "WARNING"


class InvalidCredentialsError(AuthError):
    """Invalid username or password."""

    DEFAULT_MESSAGE = "Username atau password salah."
    DEFAULT_CODE = "invalid_credentials"


class UserNotFoundError(AuthError):
    """User not found in the system."""

    DEFAULT_MESSAGE = "Pengguna tidak ditemukan."
    DEFAULT_CODE = "user_not_found"
    DEFAULT_STATUS_CODE = 404


class UserInactiveError(AuthError):
    """User account is inactive or disabled."""

    DEFAULT_MESSAGE = "Akun pengguna tidak aktif."
    DEFAULT_CODE = "user_inactive"


class PasswordMismatchError(AuthError):
    """Password does not match the stored hash."""

    DEFAULT_MESSAGE = "Password salah."
    DEFAULT_CODE = "password_mismatch"
