from __future__ import annotations

from functools import lru_cache
from typing import Callable, Protocol

from fastapi import FastAPI, Request, Response

from app.core.settings import RateLimitConfig, get_app_settings


class RateLimiter(Protocol):
    def init_app(self, app: FastAPI) -> None:
        ...

    def dependency(self, limit_value: str) -> Callable:
        ...


class NoopRateLimiter:
    def init_app(self, app: FastAPI) -> None:
        app.state.rate_limiter = self

    def dependency(self, limit_value: str) -> Callable:
        async def _noop(*_args, **_kwargs):
            return None

        return _noop


class SlowApiRateLimiter:
    def __init__(self, config: RateLimitConfig):
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        self._limiter = Limiter(
            key_func=get_remote_address,
            default_limits=config.default_limits or None,
            storage_uri=config.storage_uri,
            headers_enabled=config.headers_enabled,
        )
        self._exception_class = RateLimitExceeded
        self._exception_handler = _rate_limit_exceeded_handler

    def init_app(self, app: FastAPI) -> None:
        app.state.limiter = self._limiter
        app.state.rate_limiter = self
        app.add_exception_handler(self._exception_class, self._exception_handler)  # type: ignore[arg-type]

    def dependency(self, limit_value: str) -> Callable:
        decorated = self._limiter.limit(limit_value)

        async def _noop():
            return None

        wrapped = decorated(_noop)

        async def _dependency(request: Request, response: Response):
            return await wrapped(request=request, response=response)

        return _dependency

    @property
    def limiter(self):
        return self._limiter


class FastapiLimiterRateLimiter:
    def __init__(self, config: RateLimitConfig):
        from pyrate_limiter import Limiter

        self._config = config
        self._limiters: dict[str, Limiter] = {}

    def init_app(self, app: FastAPI) -> None:
        app.state.rate_limiter = self

    def dependency(self, limit_value: str) -> Callable:
        from fastapi_limiter.depends import RateLimiter as FastapiRateLimiter

        limiter = self._limiters.get(limit_value)
        if limiter is None:
            limiter = self._build_limiter(limit_value)
            self._limiters[limit_value] = limiter
        return FastapiRateLimiter(limiter=limiter)

    def _build_limiter(self, limit_value: str):
        from pyrate_limiter import Limiter

        rate = _parse_rate_limit(limit_value)
        return Limiter(rate)


def _parse_rate_limit(limit_value: str):
    from pyrate_limiter import Duration, Rate

    raw = limit_value.strip().lower()
    if "/" not in raw:
        raise ValueError(
            "Invalid rate limit format. Expected '<count>/<period>', e.g. '5/minute'."
        )
    count_part, period_part = [part.strip() for part in raw.split("/", 1)]
    if not count_part.isdigit():
        raise ValueError(
            "Invalid rate limit format. Expected numeric count before '/'."
        )
    count = int(count_part)

    # Accept 'minute', 'min', 'm', 'second', 'sec', 's', 'hour', 'h', 'day', 'd', 'week', 'w'
    num = ""
    unit = ""
    for ch in period_part:
        if ch.isdigit():
            num += ch
        else:
            unit += ch
    unit = unit.strip()
    multiplier = int(num) if num else 1

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
    if provider == "slowapi":
        return SlowApiRateLimiter(config)
    if provider in {"fastapi-limiter", "fastapi_limiter"}:
        return FastapiLimiterRateLimiter(config)

    raise ValueError(f"Unsupported rate limit provider: {config.provider}")


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_app_settings()
    return build_rate_limiter(settings.rate_limit)
