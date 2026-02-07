"""HTTPX client factory with retry transport."""

from __future__ import annotations

from http import HTTPStatus

from httpx import AsyncClient, Limits, Timeout
from httpx_retries import Retry, RetryTransport


def create_async_client(
    *,
    timeout: float = 10.0,
    max_connections: int = 100,
    max_keepalive: int = 20,
    retries: int = 3,
    backoff_factor: float = 0.2,
) -> AsyncClient:
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ],
    )
    transport = RetryTransport(retry=retry)
    limits = Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive)
    return AsyncClient(
        timeout=Timeout(timeout),
        limits=limits,
        transport=transport,
    )
