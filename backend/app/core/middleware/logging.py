from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import trace_id_ctx

SLOW_REQUEST_MS = 1000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request metadata with a trace id and duration."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        trace_id = (
            request.headers.get("X-Trace-Id")
            or request.headers.get("X-Request-Id")
            or uuid4().hex
        )
        request.state.trace_id = trace_id

        token = trace_id_ctx.set(trace_id)
        start = time.perf_counter()
        response: Response
        try:
            with logger.contextualize(trace_id=trace_id):
                try:
                    response = await call_next(request)
                except Exception:
                    duration_ms = int((time.perf_counter() - start) * 1000)
                    logger.bind(
                        method=request.method,
                        path=request.url.path,
                        duration_ms=duration_ms,
                    ).exception("REQUEST_FAILED")
                    raise

                duration_ms = int((time.perf_counter() - start) * 1000)
                status = response.status_code
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "-")

                bound = logger.bind(
                    method=request.method,
                    path=request.url.path,
                    status=status,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )

                if duration_ms > SLOW_REQUEST_MS:
                    bound.warning("SLOW_REQUEST")
                elif 400 <= status < 500:
                    bound.warning("REQUEST")
                elif status >= 500:
                    bound.error("REQUEST")
                else:
                    bound.info("REQUEST")

                response.headers["X-Trace-Id"] = trace_id
                return response
        finally:
            trace_id_ctx.reset(token)
