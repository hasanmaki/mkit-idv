"""Exception handlers for FastAPI application."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions.base import AppBaseExceptionError
from app.core.settings import get_app_settings


def _extract_trace_id(request: Request) -> str:
    """Extract trace_id from request state or headers; generate if missing."""
    trace_id = getattr(request.state, "trace_id", None)
    if not trace_id:
        trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = request.headers.get("X-Request-Id")
    return trace_id or uuid4().hex


def _build_response(payload: dict, status_code: int, trace_id: str) -> JSONResponse:
    response = JSONResponse(status_code=status_code, content=payload)
    response.headers["X-Trace-Id"] = trace_id
    return response


def make_app_base_exception_handler(logger_):
    async def handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: RUF029
        """Handle AppBaseExceptionError and return JSON response."""
        assert isinstance(exc, AppBaseExceptionError)
        settings = get_app_settings()
        trace_id = _extract_trace_id(request)
        bound = logger_.bind(
            trace_id=trace_id,
            error=exc.__class__.__name__,
            error_code=exc.error_code,
            status=exc.status_code,
        )
        bound.opt(exception=exc.original_exception or exc).log(
            exc.DEFAULT_LOG_LEVEL,
            "APPLICATION_ERROR | {name} | {msg} | context={ctx}",
            name=exc.__class__.__name__,
            msg=str(exc),
            ctx=exc.context,
        )
        payload = exc.to_response_payload(trace_id=trace_id, debug=settings.debug)
        payload["datetime"] = datetime.now(UTC).isoformat()
        return _build_response(payload, exc.status_code, trace_id)

    return handler


def make_http_exception_handler(logger_):
    async def handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: RUF029
        """Handle FastAPI HTTPException and return JSON response."""
        assert isinstance(exc, HTTPException)
        trace_id = _extract_trace_id(request)
        level = "WARNING" if 400 <= exc.status_code < 500 else "ERROR"
        bound = logger_.bind(trace_id=trace_id, status=exc.status_code)
        bound.log(
            level,
            "HTTP_ERROR | {status} | {detail} | path={path}",
            status=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )
        message = exc.detail if isinstance(exc.detail, str) else "Permintaan tidak valid."
        payload = {
            "success": False,
            "error": "HTTPException",
            "error_code": "http_error",
            "message": message,
            "trace_id": trace_id,
            "datetime": datetime.now(UTC).isoformat(),
        }
        return _build_response(payload, exc.status_code, trace_id)

    return handler


def make_unexpected_exception_handler(logger_):
    async def handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: RUF029
        """Handle unexpected Exception and return generic JSON response."""
        trace_id = _extract_trace_id(request)
        bound = logger_.bind(trace_id=trace_id, path=request.url.path)
        bound.opt(exception=exc).critical(
            "UNEXPECTED_ERROR | {type} | {exc!r} | path={path}",
            type=exc.__class__.__name__,
            exc=exc,
            path=request.url.path,
        )
        payload = {
            "success": False,
            "error": "InternalServerError",
            "error_code": "internal_error",
            "message": "Terjadi kesalahan sistem internal.",
            "trace_id": trace_id,
            "datetime": datetime.now(UTC).isoformat(),
        }
        return _build_response(payload, 500, trace_id)

    return handler


def register_exception_handlers(app: FastAPI, logger_: object | None = None) -> None:
    """Register clean exception handlers for FastAPI app.

    Accepts an optional logger to bind trace ids and other context. If not
    provided, uses module-level `logger` from loguru.
    """
    logger_ = logger_ or logger
    app.add_exception_handler(
        AppBaseExceptionError, make_app_base_exception_handler(logger_)
    )
    app.add_exception_handler(HTTPException, make_http_exception_handler(logger_))
    app.add_exception_handler(Exception, make_unexpected_exception_handler(logger_))
