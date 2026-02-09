from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache
from typing import Protocol, cast

import anyio
from fastapi import FastAPI
from fastapi_limiter.depends import RateLimiter as FastapiRateLimiter
from pyrate_limiter import Duration, Limiter, Rate

from app.core.settings import RateLimitConfig, get_app_settings


class RateLimiter(Protocol):
    def init_app(self, app: FastAPI) -> None: ...

    def dependency(self, limit_value: str) -> Callable: ...


class NoopRateLimiter:
    def init_app(self, app: FastAPI) -> None:
        app.state.rate_limiter = self

    def dependency(self, limit_value: str) -> Callable:
        async def _noop(*_args, **_kwargs):
            return None

        return _noop


class FastapiLimiterRateLimiter:
    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._limiters: dict[str, Limiter] = {}

    def init_app(self, app: FastAPI) -> None:
        app.state.rate_limiter = self

    def dependency(self, limit_value: str) -> Callable:
        limiter = self._limiters.get(limit_value)
        if limiter is None:
            limiter = self._build_limiter(limit_value)
            self._limiters[limit_value] = limiter
        # fastapi_limiter expects try_acquire_async(key, blocking=False)
        return FastapiRateLimiter(limiter=cast(Limiter, _LimiterAdapter(limiter)))

    def _build_limiter(self, limit_value: str):
        rate = _parse_rate_limit(limit_value)
        return Limiter(rate)


class _LimiterAdapter:
    """Adapter around pyrate_limiter.Limiter to expose the async
    try_acquire_async(key, blocking=False) API expected by
    fastapi_limiter.depends.RateLimiter.

    We keep the adapter minimal — we ignore the `blocking` argument
    because the pyrate limiter used here doesn't support blocking
    semantics in async APIs; tests expect non-blocking behavior.
    """

    def __init__(self, limiter: Limiter):
        self._limiter = limiter

    async def try_acquire_async(self, key: str, blocking: bool = False) -> bool:
        """Call the synchronous limiter in a thread to avoid blocking the event loop.

        Note: the ``blocking`` argument is intentionally ignored — the
        underlying ``pyrate_limiter.Limiter`` used here does not provide
        an async blocking API. If you need true blocking semantics, we can
        implement a retry/wait loop or swap to a limiter with that support.
        """
        return await anyio.to_thread.run_sync(self._limiter.try_acquire, key)


_RATE_RE = re.compile(r"^\s*(\d+)\s*/\s*([0-9]*)([a-z]+)\s*$", re.I)


def _parse_rate_limit(limit_value: str):
    match = _RATE_RE.match(limit_value)
    if not match:
        raise ValueError(
            "Invalid rate limit format. Expected '<count>/<period>', e.g. '5/minute'."
        )
    count = int(match.group(1))
    multiplier = int(match.group(2)) if match.group(2) else 1
    unit = match.group(3).lower()

    unit_map = {
        "second": Duration.SECOND,
        "seconds": Duration.SECOND,
        "sec": Duration.SECOND,
        "s": Duration.SECOND,
        "minute": Duration.MINUTE,
        "minutes": Duration.MINUTE,
        "min": Duration.MINUTE,
        "m": Duration.MINUTE,
        "hour": Duration.HOUR,
        "hours": Duration.HOUR,
        "h": Duration.HOUR,
        "day": Duration.DAY,
        "days": Duration.DAY,
        "d": Duration.DAY,
        "week": Duration.DAY,
        "weeks": Duration.DAY,
        "w": Duration.DAY,
    }
    if unit not in unit_map:
        raise ValueError(
            "Invalid rate limit period unit. Use second/minute/hour/day/week."
        )

    duration = unit_map[unit] * multiplier
    if unit in {"week", "weeks", "w"}:
        duration = Duration.DAY * 7 * multiplier

    return Rate(count, duration)


def build_rate_limiter(config: RateLimitConfig) -> RateLimiter:
    if not config.enabled or config.provider.lower() in {"none", "disabled"}:
        return NoopRateLimiter()

    provider = config.provider.lower()
    if provider in {"fastapi-limiter", "fastapi_limiter"}:
        return FastapiLimiterRateLimiter(config)

    raise ValueError(f"Unsupported rate limit provider: {config.provider}")


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_app_settings()
    return build_rate_limiter(settings.rate_limit)
