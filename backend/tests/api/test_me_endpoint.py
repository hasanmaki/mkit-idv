"""Tests for /me endpoint."""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from app.api.deps import get_current_user
from app.api.v1.me import router as me_router


class DummyUser:
    def __init__(self):
        self.id = 1
        self.name = "User"
        self.username = "user1"
        self.email = "user1@example.com"
        self.is_admin = False
        self.is_active = True


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(me_router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_me_endpoint(app: FastAPI) -> None:
    app.dependency_overrides[get_current_user] = lambda: DummyUser()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/me")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["username"] == "user1"
