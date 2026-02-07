"""HTTPX client factory with retry transport."""

from __future__ import annotations

from http import HTTPStatus

from httpx import AsyncClient, Limits, Timeout
from httpx_retries import Retry, RetryTransport

from app.core.settings import HttpxConfig


def create_async_client(config: HttpxConfig) -> AsyncClient:
    """Create an HTTPX AsyncClient with retry transport."""
    retry = Retry(
        total=config.retries,
        backoff_factor=config.backoff_factor,
        status_forcelist=[
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ],
    )
    transport = RetryTransport(retry=retry)
    limits = Limits(
        max_connections=config.max_connections,
        max_keepalive_connections=config.max_keepalive,
    )
    timeout = Timeout(config.timeout_seconds)
    return AsyncClient(
        transport=transport,
        limits=limits,
        timeout=timeout,
    )
