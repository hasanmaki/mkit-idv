# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Authentication Service.

This module provides high-level authentication orchestration including login,
token refresh, and logout operations. It coordinates between JwtService,
SessionService, and UserRepository to provide a complete authentication flow.

Key Design:
- JWT for access tokens (stateless, short-lived)
- Opaque tokens for refresh (stored in database, revocable)
- Clear separation of concerns: JwtService (crypto), SessionService (state),
  AuthService (orchestration)
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.logging import get_logger
from app.core.settings import JwtConfig
from app.models.users import User
from app.repositories import UserRepository
from app.services.auth.auth_schemas import LoginResponse, RefreshTokenResponse
from app.services.jwt.jwt_service import JwtService
from app.services.sessions.session_schemas import SessionCreate
from app.services.sessions.session_services import SessionService

logger = get_logger("service.auth")


class AuthService:
    """Service for authentication operations.

    This service orchestrates the authentication flow by coordinating
    between JWT service, session service, and user repository.

    Attributes:
        jwt (JwtService): Service for JWT token operations.
        sessions (SessionService): Service for session management.
        users (UserRepository): Repository for user data access.

    Methods:
        login: Authenticate user and return tokens.
        refresh_tokens: Refresh access token using refresh token.
        logout: Revoke user session.

    """

    def __init__(
        self,
        jwt_service: JwtService,
        session_service: SessionService,
        user_repo: UserRepository,
        jwt_config: JwtConfig,
    ) -> None:
        self.jwt = jwt_service
        self.sessions = session_service
        self.users = user_repo
        self._jwt_config = jwt_config

    def _now(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.now(UTC)

    async def login(
        self,
        user: User,
        ip: str | None = None,
        ua: str | None = None,
    ) -> LoginResponse:
        """Authenticate user and return tokens.

        This method:
        1. Generates an opaque refresh token (plaintext + hash)
        2. Creates a session with the hashed refresh token
        3. Creates a JWT access token
        4. Returns both tokens to the client

        Args:
            user (User): The authenticated user entity.
            ip (str | None): The client's IP address for audit.
            ua (str | None): The client's user agent for audit.

        Returns:
            LoginResponse: Response containing access_token and refresh_token.

        Raises:
            UserInactiveError: If the user account is inactive.
        """
        # Check if user is active
        if not user.is_active:
            from app.services.auth.auth_errors import UserInactiveError

            logger.warning("Login rejected: inactive account, user_id={}", user.id)
            raise UserInactiveError(context={"user_id": user.id})

        # Generate opaque refresh token (plaintext + hash)
        refresh_token, refresh_hash = self.jwt.generate_refresh_token()
        session_id = uuid4().hex

        # Calculate session expiration (refresh token lifetime)
        expires_at = self._now() + timedelta(
            minutes=self._jwt_config.refresh_token_expire_minutes
        )

        # Create session with hashed refresh token
        await self.sessions.create_session(
            SessionCreate(
                user_id=user.id,
                session_id=session_id,
                refresh_token_hash=refresh_hash,
                expires_at=expires_at,
                ip_address=ip,
                user_agent=ua,
            )
        )

        # Create JWT access token
        access_token = self.jwt.create_access_token(
            user_id=user.id,
            session_id=session_id,
        )

        logger.info("User logged in, user_id={}, session_id={}", user.id, session_id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip: str | None = None,
        ua: str | None = None,
    ) -> RefreshTokenResponse:
        """Refresh access token using refresh token.

        This method:
        1. Verifies the access token to get session_id
        2. Validates the session and refresh token hash
        3. Generates new tokens
        4. Updates session with new refresh token hash

        Args:
            refresh_token (str): The opaque refresh token.
            ip (str | None): The client's IP address for audit.
            ua (str | None): The client's user agent for audit.

        Returns:
            RefreshTokenResponse: Response containing new access_token and refresh_token.

        Raises:
            SessionNotFoundError: If the session is not found.
            SessionRevokedError: If the session has been revoked.
            SessionExpiredError: If the session has expired.
        """
        refresh_hash = self.jwt.hash_refresh_token(refresh_token)

        session = await self.sessions.validate_refresh_token_hash(refresh_hash)

        new_refresh_token, new_refresh_hash = self.jwt.generate_refresh_token()
        now = self._now()
        new_expires_at = now + timedelta(
            minutes=self._jwt_config.refresh_token_expire_minutes
        )

        session.refresh_token_hash = new_refresh_hash
        session.expires_at = new_expires_at
        session.last_activity_at = now
        if ip is not None:
            session.ip_address = ip
        if ua is not None:
            session.user_agent = ua
        await self.sessions.repo.save()

        access_token = self.jwt.create_access_token(
            user_id=session.user_id,
            session_id=session.session_id,
        )

        logger.debug("Tokens refreshed, session_id={}", session.session_id)

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        """Revoke user session.

        Args:
            refresh_token (str): The refresh token to revoke.

        Raises:
            SessionNotFoundError: If the session is not found.
        """
        refresh_hash = self.jwt.hash_refresh_token(refresh_token)
        session = await self.sessions.validate_refresh_token_hash(refresh_hash)
        await self.sessions.revoke_session(session.session_id)
        logger.info("User logged out, session_id={}", session.session_id)
