"""Tests for auth admin endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from app.api.deps import get_session_service, require_admin
from app.api.v1.auth import router as auth_router
from fastapi import FastAPI


class DummySession:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class DummySessionService:
    def __init__(self):
        self.revoked_session_id: str | None = None
        self.revoked_user_id: int | None = None
        self.sessions = [
            DummySession(
                session_id="s1",
                is_revoked=False,
                expires_at=datetime.now(UTC),
                last_activity_at=None,
                ip_address=None,
                user_agent=None,
            )
        ]

    async def revoke_session(self, session_id: str) -> None:
        self.revoked_session_id = session_id

    async def revoke_all_sessions_for_user(self, user_id: int) -> int:
        self.revoked_user_id = user_id
        return 2

    async def list_sessions_for_user(self, user_id: int):
        self.revoked_user_id = user_id
        return self.sessions


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_admin_revoke_session(app: FastAPI) -> None:
    service = DummySessionService()
    app.dependency_overrides[get_session_service] = lambda: service
    app.dependency_overrides[require_admin] = lambda: object()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/admin/revoke-session",
            json={"session_id": "abc"},
        )

    assert resp.status_code == 204
    assert service.revoked_session_id == "abc"


@pytest.mark.asyncio
async def test_admin_revoke_user_sessions(app: FastAPI) -> None:
    service = DummySessionService()
    app.dependency_overrides[get_session_service] = lambda: service
    app.dependency_overrides[require_admin] = lambda: object()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/admin/revoke-user-sessions",
            json={"user_id": 42},
        )

    assert resp.status_code == 200
    assert resp.json() == {"revoked": 2}
    assert service.revoked_user_id == 42


@pytest.mark.asyncio
async def test_admin_list_sessions(app: FastAPI) -> None:
    service = DummySessionService()
    app.dependency_overrides[get_session_service] = lambda: service
    app.dependency_overrides[require_admin] = lambda: object()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/admin/sessions", params={"user_id": 7})

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["session_id"] == "s1"
