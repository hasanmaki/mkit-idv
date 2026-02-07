"""Tests for auth endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from app.api.deps import get_auth_service, get_password_hasher, get_user_repo
from app.api.v1.auth import router as auth_router
from app.core.utils.hashing import get_password_hasher as core_hasher
from app.core.settings import JwtConfig
from app.services.auth.auth_services import AuthService
from app.services.jwt import JwtService
from app.services.sessions.session_services import SessionService


class DummyUser:
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        hashed_password: str,
        is_active: bool = True,
    ):
        self.id = user_id
        self.name = "Dummy"
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_admin = False
        self.is_active = is_active


class DummyUserRepo:
    def __init__(self, user: DummyUser):
        self.user = user

    async def get_by_username(self, username: str):
        if self.user.username == username:
            return self.user
        return None

    async def get_by_email(self, email: str):
        if self.user.email == email:
            return self.user
        return None

    async def get_by_id(self, user_id: int):
        if self.user.id == user_id:
            return self.user
        return None


class DummySessionRepo:
    def __init__(self):
        self.sessions = {}

    async def add(self, session):
        self.sessions[session.session_id] = session

    async def get_by_session_id(self, session_id):
        return self.sessions.get(session_id)

    async def get_by_refresh_token_hash(self, refresh_token_hash):
        for session in self.sessions.values():
            if session.refresh_token_hash == refresh_token_hash:
                return session
        return None

    async def save(self):
        return None

    async def list_by_user_id(self, user_id: int):
        return [s for s in self.sessions.values() if s.user_id == user_id]


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    return app


@pytest.fixture
def jwt_config() -> JwtConfig:
    return JwtConfig(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
        access_token_expire_minutes=5,
        refresh_token_expire_minutes=60,
    )


@pytest.fixture
def auth_service(jwt_config: JwtConfig) -> AuthService:
    jwt_service = JwtService(jwt_config)
    session_repo = DummySessionRepo()
    session_service = SessionService(session_repo)
    user_repo = DummyUserRepo(
        DummyUser(
            user_id=1,
            username="user1",
            email="user1@example.com",
            hashed_password=core_hasher().hash("secret"),
        )
    )
    return AuthService(
        jwt_service=jwt_service,
        session_service=session_service,
        user_repo=user_repo,
        jwt_config=jwt_config,
    )


@pytest.mark.asyncio
async def test_login_refresh_logout_flow(app: FastAPI, auth_service: AuthService) -> None:
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_user_repo] = lambda: auth_service.users
    app.dependency_overrides[get_password_hasher] = lambda: core_hasher()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "user1", "password": "secret"},
        )

        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": data["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        refreshed = refresh_resp.json()
        assert refreshed["access_token"]
        assert refreshed["refresh_token"]

        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refreshed["refresh_token"]},
        )
        assert logout_resp.status_code == 204
