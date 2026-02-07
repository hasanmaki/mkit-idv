"""Tests for AuthService."""

from datetime import UTC, datetime, timedelta

import pytest
from app.core.settings import JwtConfig
from app.services.auth.auth_services import AuthService
from app.services.jwt import JwtService
from app.services.sessions.session_services import SessionService
from faker import Faker
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


class DummyRepo:
    def __init__(self):
        self.sessions = {}
        self.saved = False

    async def get_by_session_id(self, session_id):
        return self.sessions.get(session_id)

    async def get_by_refresh_token_hash(self, refresh_token_hash):
        for session in self.sessions.values():
            if session.refresh_token_hash == refresh_token_hash:
                return session
        return None

    async def save(self):
        self.saved = True


class DummyUserRepo:
    pass


@pytest.fixture
def faker() -> Faker:
    return Faker()


@pytest.fixture
def jwt_config() -> JwtConfig:
    return JwtConfig(
        secret_key=SecretStr("test-secret-key-for-testing-only"),
        algorithm="HS256",
        access_token_expire_minutes=5,
        refresh_token_expire_minutes=60,
    )


@pytest.fixture
def jwt_service(jwt_config: JwtConfig) -> JwtService:
    return JwtService(jwt_config)


@pytest.fixture
def repo() -> DummyRepo:
    return DummyRepo()


@pytest.fixture
def session_service(repo: DummyRepo) -> SessionService:
    return SessionService(repo)


@pytest.fixture
def auth_service(
    jwt_service: JwtService, session_service: SessionService, jwt_config: JwtConfig
) -> AuthService:
    return AuthService(
        jwt_service=jwt_service,
        session_service=session_service,
        user_repo=DummyUserRepo(),
        jwt_config=jwt_config,
    )


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_refresh_token(
    auth_service: AuthService, jwt_service: JwtService, repo: DummyRepo, faker: Faker
) -> None:
    now = datetime.now(UTC)
    session_id = faker.uuid4()
    user_id = faker.random_int()
    refresh_token, refresh_hash = jwt_service.generate_refresh_token()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_hash,
        expires_at=now + timedelta(minutes=30),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session

    result = await auth_service.refresh_tokens(
        refresh_token=refresh_token,
        ip="127.0.0.1",
        ua="pytest-agent",
    )

    assert result.access_token
    assert result.refresh_token
    assert result.refresh_token != refresh_token
    assert session.refresh_token_hash != refresh_hash
    assert session.expires_at > now
    assert session.last_activity_at is not None
    assert session.ip_address == "127.0.0.1"
    assert session.user_agent == "pytest-agent"
    assert repo.saved is True


@pytest.mark.asyncio
async def test_logout_revokes_session(
    auth_service: AuthService, jwt_service: JwtService, repo: DummyRepo, faker: Faker
) -> None:
    now = datetime.now(UTC)
    session_id = faker.uuid4()
    user_id = faker.random_int()
    refresh_token, refresh_hash = jwt_service.generate_refresh_token()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_hash,
        expires_at=now + timedelta(minutes=30),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session

    await auth_service.logout(refresh_token=refresh_token)

    assert session.is_revoked is True
    assert session.revoked_at is not None
    assert repo.saved is True
