# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
"""Application error cases."""

from ..core.exceptions.base import AppBaseExceptionError


class DatabaseError(AppBaseExceptionError):
    """Custom exception for database-related errors."""

    DEFAULT_MESSAGE = "Operasi database gagal."
    DEFAULT_STATUS_CODE = 500
    DEFAULT_CODE = "db_error"


class DatabaseUnavailableError(DatabaseError):
    """Database dependency unavailable or not ready."""

    DEFAULT_MESSAGE = "Layanan database tidak tersedia."
    DEFAULT_STATUS_CODE = 503
    DEFAULT_CODE = "db_unavailable"


class DatabaseInternalError(DatabaseError):
    """Database internal error (unexpected/bug)."""

    DEFAULT_MESSAGE = "Terjadi kesalahan internal pada database."
    DEFAULT_STATUS_CODE = 500
    DEFAULT_CODE = "db_internal_error"
