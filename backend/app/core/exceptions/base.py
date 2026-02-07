# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Base exceptions used across the application."""

from typing import Any


class AppBaseExceptionError(Exception):
    """Base class for all application-specific exceptions.

    Design principles:
    - Transport-aware (HTTP status code defined at class level)
    - Stable error code contract for frontend + logs
    - Safe to be raised from any layer (domain / service / infra)

    Attributes:
        DEFAULT_STATUS_CODE: HTTP status code associated with the error.
        DEFAULT_MESSAGE: Default human-readable error message (client-facing).
        DEFAULT_CODE: Stable application error code for frontend & logs.
        DEFAULT_LOG_LEVEL: Loguru level name to use when logging.
        EXPOSE_CONTEXT: Whether context may be returned to clients in debug.
    """

    DEFAULT_STATUS_CODE: int = 500
    DEFAULT_MESSAGE: str = "Terjadi kesalahan pada aplikasi."
    DEFAULT_CODE: str = "app_error"
    DEFAULT_LOG_LEVEL: str = "WARNING"
    EXPOSE_CONTEXT: bool = False

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message or self.DEFAULT_MESSAGE)
        self.context: dict[str, Any] = context or {}
        self.original_exception: Exception | None = original_exception
        self.error_code: str = error_code or self.DEFAULT_CODE

    @property
    def status_code(self) -> int:
        """HTTP status code associated with this exception."""
        return self.DEFAULT_STATUS_CODE

    def to_response_payload(self, trace_id: str, debug: bool) -> dict[str, Any]:
        """Serialize exception for API responses."""
        payload: dict[str, Any] = {
            "success": False,
            "error": self.__class__.__name__,
            "error_code": self.error_code,
            "message": str(self),
            "trace_id": trace_id,
        }
        if debug and self.EXPOSE_CONTEXT and self.context:
            payload["context"] = self.context
        return payload

    def to_log_payload(self, trace_id: str) -> dict[str, Any]:
        """Serialize exception for structured logging."""
        return {
            "type": self.__class__.__name__,
            "message": str(self),
            "status_code": self.status_code,
            "context": self.context,
            "original_exception": repr(self.original_exception),
            "error_code": self.error_code,
            "trace_id": trace_id,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={str(self)!r}, "
            f"context={self.context!r}, "
            f"original_exception={self.original_exception!r}, "
            f"error_code={self.error_code!r})"
        )
