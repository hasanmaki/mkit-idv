"""Tests for auth dependencies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.api.deps import get_current_user
from app.core.settings import JwtConfig
from app.services.jwt import JwtService
from app.services.sessions.session_services import SessionService
from pydantic import SecretStr


class DummySession:
    def __init__(self, **kwargs):
        self.last_activity_at = kwargs.get("last_activity_at")
        self.revoked_at = kwargs.get("revoked_at")
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def is_revoked(self):
        return self.__dict__.get("_is_revoked", self.__dict__.get("is_revoked", False))

    @is_revoked.setter
    def is_revoked(self, value):
        self.__dict__["_is_revoked"] = value


class DummySessionRepo:
    def __init__(self):
        self.sessions = {}

    async def get_by_session_id(self, session_id):
        return self.sessions.get(session_id)

    async def save(self):
        return None


class DummyUser:
    def __init__(self, user_id: int, is_active: bool = True):
        self.id = user_id
        self.is_active = is_active
        self.is_admin = False


class DummyUserRepo:
    def __init__(self, user):
        self.user = user

    async def get_by_id(self, user_id: int):
        if self.user and self.user.id == user_id:
            return self.user
        return None


@pytest.mark.asyncio
async def test_get_current_user_success() -> None:
    jwt_service = JwtService(
        JwtConfig(
            secret_key=SecretStr("test-secret"),
            algorithm="HS256",
            access_token_expire_minutes=5,
            refresh_token_expire_minutes=60,
        )
    )
    repo = DummySessionRepo()
    session_service = SessionService(repo)

    user_id = 1
    session_id = "sess-1"
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash="hash",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session

    token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)
    user_repo = DummyUserRepo(DummyUser(user_id))

    user = await get_current_user(
        token=token,
        jwt_service=jwt_service,
        session_service=session_service,
        user_repo=user_repo,
    )

    assert user.id == user_id


@pytest.mark.asyncio
async def test_get_current_user_missing_token() -> None:
    jwt_service = JwtService(
        JwtConfig(
            secret_key=SecretStr("test-secret"),
            algorithm="HS256",
            access_token_expire_minutes=5,
            refresh_token_expire_minutes=60,
        )
    )
    repo = DummySessionRepo()
    session_service = SessionService(repo)
    user_repo = DummyUserRepo(DummyUser(1))

    with pytest.raises(HTTPException):
        await get_current_user(
            token="invalid",
            jwt_service=jwt_service,
            session_service=session_service,
            user_repo=user_repo,
        )
