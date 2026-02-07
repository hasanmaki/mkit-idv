# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    get_auth_service,
    get_password_hasher,
    get_session_service,
    get_user_repo,
    require_admin,
)
from app.repositories import UserRepository
from app.services.auth.auth_errors import InvalidCredentialsError
from app.services.auth.auth_schemas import (
    AdminRevokeSessionInput,
    AdminRevokeUserSessionsInput,
    LoginInput,
    LoginResponse,
    LogoutInput,
    RefreshTokenInput,
    RefreshTokenResponse,
)
from app.services.auth.auth_services import AuthService
from app.services.sessions.session_schemas import SessionPublic
from app.services.sessions.session_services import SessionService
from pwdlib import PasswordHash

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and issue tokens",
)
async def login(
    data: LoginInput,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    users: UserRepository = Depends(get_user_repo),
    password_hasher: PasswordHash = Depends(get_password_hasher),
) -> LoginResponse:
    """Authenticate user and return access + refresh tokens."""
    if "@" in data.username:
        user = await users.get_by_email(data.username)
    else:
        user = await users.get_by_username(data.username)

    if user is None:
        raise InvalidCredentialsError()

    if not password_hasher.verify(data.password, user.hashed_password):
        raise InvalidCredentialsError()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await auth.login(user=user, ip=ip, ua=ua)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_tokens(
    data: RefreshTokenInput,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    """Refresh access token using refresh token."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await auth.refresh_tokens(refresh_token=data.refresh_token, ip=ip, ua=ua)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke session",
)
async def logout(
    data: LogoutInput,
    auth: AuthService = Depends(get_auth_service),
) -> None:
    """Revoke session using refresh token."""
    await auth.logout(refresh_token=data.refresh_token)


@router.post(
    "/admin/revoke-session",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin revoke a session",
)
async def admin_revoke_session(
    data: AdminRevokeSessionInput,
    _: object = Depends(require_admin),
    sessions: SessionService = Depends(get_session_service),
) -> None:
    """Revoke a session by session_id."""
    await sessions.revoke_session(data.session_id)


@router.post(
    "/admin/revoke-user-sessions",
    status_code=status.HTTP_200_OK,
    summary="Admin revoke all sessions for a user",
)
async def admin_revoke_user_sessions(
    data: AdminRevokeUserSessionsInput,
    _: object = Depends(require_admin),
    sessions: SessionService = Depends(get_session_service),
) -> dict[str, int]:
    """Revoke all sessions for a user. Returns count revoked."""
    revoked = await sessions.revoke_all_sessions_for_user(data.user_id)
    return {"revoked": revoked}


@router.get(
    "/admin/sessions",
    response_model=list[SessionPublic],
    status_code=status.HTTP_200_OK,
    summary="Admin list sessions for a user",
)
async def admin_list_sessions(
    user_id: int,
    _: object = Depends(require_admin),
    sessions: SessionService = Depends(get_session_service),
) -> list[SessionPublic]:
    """List sessions for a given user_id."""
    items = await sessions.list_sessions_for_user(user_id)
    return [SessionPublic.model_validate(session) for session in items]
