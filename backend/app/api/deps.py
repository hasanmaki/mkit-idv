# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""API dependency providers."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import JwtConfig, get_app_settings
from app.core.utils.hashing import get_password_hasher as _get_password_hasher
from app.repositories import SessionRepository, UserRepository
from app.services.auth.auth_services import AuthService
from app.services.jwt import JwtService
from app.services.sessions.session_services import SessionService


@lru_cache
def get_jwt_config() -> JwtConfig:
    return get_app_settings().jwt


def get_jwt_service(jwt_config: JwtConfig = Depends(get_jwt_config)) -> JwtService:
    return JwtService(jwt_config)


def get_password_hasher():
    return _get_password_hasher()


async def get_db_session_dep() -> AsyncSession:
    from app.database.session import get_db_session

    async for session in get_db_session():
        yield session


def get_session_repo(
    db: AsyncSession = Depends(get_db_session_dep),
) -> SessionRepository:
    return SessionRepository(db)


def get_user_repo(
    db: AsyncSession = Depends(get_db_session_dep),
) -> UserRepository:
    return UserRepository(db)


def get_session_service(
    repo: SessionRepository = Depends(get_session_repo),
) -> SessionService:
    return SessionService(repo)


def get_auth_service(
    jwt_service: JwtService = Depends(get_jwt_service),
    session_service: SessionService = Depends(get_session_service),
    user_repo: UserRepository = Depends(get_user_repo),
    jwt_config: JwtConfig = Depends(get_jwt_config),
) -> AuthService:
    return AuthService(
        jwt_service=jwt_service,
        session_service=session_service,
        user_repo=user_repo,
        jwt_config=jwt_config,
    )


def get_httpx_client(request: Request) -> AsyncClient:
    client = getattr(request.app.state, "httpx", None)
    if client is None:
        raise RuntimeError("HTTPX client not initialized in app.state")
    return client


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_service: JwtService = Depends(get_jwt_service),
    session_service: SessionService = Depends(get_session_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    payload = jwt_service.verify_access_token(token)
    session = await session_service.validate_session(payload.session_id)

    user = await user_repo.get_by_id(session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    return user


async def require_admin(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
