"""a testing module for session services."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.sessions.session_errors import (
    RefreshTokenMismatchError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError,
)
from app.services.sessions.session_schemas import SessionCreate, SessionValidationResult
from app.services.sessions.session_services import SessionService
from faker import Faker


class DummySession:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DummyRepo:
    def __init__(self):
        self.sessions = {}
        self.saved = False

    async def add(self, session):
        self.sessions[session.session_id] = session

    async def get_by_session_id(self, session_id):
        return self.sessions.get(session_id)

    async def save(self):
        self.saved = True


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture
def repo():
    return DummyRepo()


@pytest.fixture
def service(repo):
    return SessionService(repo)


@pytest.mark.asyncio
async def test_create_and_validate_session(service, repo, faker):
    now = datetime.now(UTC)
    user_id = faker.random_int()
    session_id = faker.uuid4()
    refresh_token_hash = faker.sha256()
    ip_address = faker.ipv4()
    user_agent = faker.user_agent()
    data = SessionCreate(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=now + timedelta(hours=1),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session = await service.create_session(data)
    assert session.session_id == session_id
    assert repo.sessions[session_id] == session

    # Validate session
    result = await service.validate_session(session_id)
    assert isinstance(result, SessionValidationResult)
    assert result.user_id == user_id
    assert result.session_id == session_id


@pytest.mark.asyncio
async def test_validate_session_not_found(service, faker):
    session_id = faker.uuid4()
    with pytest.raises(SessionNotFoundError):
        await service.validate_session(session_id)


@pytest.mark.asyncio
async def test_validate_session_revoked(service, repo, faker):
    now = datetime.now(UTC)
    user_id = faker.random_int()
    session_id = faker.uuid4()
    refresh_token_hash = faker.sha256()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=now + timedelta(hours=1),
        is_revoked=True,
        revoked_at=now,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session
    with pytest.raises(SessionRevokedError):
        await service.validate_session(session_id)


@pytest.mark.asyncio
async def test_validate_session_expired(service, repo, faker):
    now = datetime.now(UTC)
    user_id = faker.random_int()
    session_id = faker.uuid4()
    refresh_token_hash = faker.sha256()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=now - timedelta(seconds=1),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session
    with pytest.raises(SessionExpiredError):
        await service.validate_session(session_id)


@pytest.mark.asyncio
async def test_validate_refresh_token_success(service, repo, faker):
    now = datetime.now(UTC)
    user_id = faker.random_int()
    session_id = faker.uuid4()
    refresh_token_hash = faker.sha256()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=now + timedelta(hours=1),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session
    result = await service.validate_refresh_token(
        session_id=session_id, refresh_token_hash=refresh_token_hash
    )
    assert result == session


@pytest.mark.asyncio
async def test_validate_refresh_token_mismatch(service, repo, faker):
    now = datetime.now(UTC)
    user_id = faker.random_int()
    session_id = faker.uuid4()
    refresh_token_hash = faker.sha256()
    session = DummySession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=now + timedelta(hours=1),
        is_revoked=False,
        revoked_at=None,
        last_activity_at=None,
        ip_address=None,
        user_agent=None,
    )
    repo.sessions[session_id] = session
    with pytest.raises(RefreshTokenMismatchError):
        await service.validate_refresh_token(
            session_id=session_id, refresh_token_hash=faker.sha256()
        )
