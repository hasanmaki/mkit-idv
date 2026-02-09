# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Module Title.

Short description of this module and its responsibilities. Explain its purpose within the application architecture.

Key Features:
    - First key feature
    - Second key feature

Attributes:
    - Second key feature
    - Second key feature

Example:
    from module import something

Note:
    - Important constraints or considerations
"""

from datetime import UTC, datetime
from hmac import compare_digest

from app.core.logging import get_logger
from app.models.sessions import Session
from app.repositories import SessionRepository
from app.services.sessions.session_errors import (
    RefreshTokenMismatchError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError,
)
from app.services.sessions.session_schemas import SessionCreate, SessionValidationResult

logger = get_logger("service.session")


class SessionService:
    """Business logic for session lifecycle."""

    def __init__(self, repo: SessionRepository):
        self.repo = repo

    def _now(self) -> datetime:
        return datetime.now(UTC)

    async def create_session(self, data: SessionCreate) -> Session:
        """Create a new session."""
        session = await self.repo.create(data)
        logger.debug(
            "Session created, session_id={}, user_id={}", data.session_id, data.user_id
        )
        return session

    async def validate_session(self, session_id: str) -> SessionValidationResult:
        """Validate an existing session."""
        session = await self.repo.get_by_session_id(session_id)

        if not session:
            logger.warning(
                "Session validation failed: not found, session_id={}", session_id
            )
            raise SessionNotFoundError(context={"session_id": session_id})

        if session.is_revoked:
            logger.warning(
                "Session validation failed: revoked, session_id={}", session_id
            )
            raise SessionRevokedError(
                context={"session_id": session_id, "revoked_at": session.revoked_at}
            )

        if session.expires_at <= self._now():
            logger.warning(
                "Session validation failed: expired, session_id={}", session_id
            )
            raise SessionExpiredError(context={"session_id": session_id})

        session.last_activity_at = self._now()
        await self.repo.save()

        return SessionValidationResult(
            user_id=session.user_id,
            session_id=session.session_id,
        )

    async def validate_refresh_token(
        self,
        *,
        session_id: str,
        refresh_token_hash: str,
    ) -> Session:
        """Validate a refresh token for a session."""
        session = await self.repo.get_by_session_id(session_id)

        if not session:
            raise SessionNotFoundError(context={"session_id": session_id})

        if session.is_revoked:
            raise SessionRevokedError(context={"session_id": session_id})

        if session.expires_at <= self._now():
            raise SessionExpiredError(context={"session_id": session_id})

        if not compare_digest(session.refresh_token_hash, refresh_token_hash):
            raise RefreshTokenMismatchError(context={"session_id": session_id})

        return session

    async def validate_refresh_token_hash(self, refresh_token_hash: str) -> Session:
        """Validate a refresh token hash and return its session."""
        session = await self.repo.get_by_refresh_token_hash(refresh_token_hash)

        if not session:
            logger.warning("Refresh token validation failed: session not found")
            raise SessionNotFoundError(context={"refresh_token_hash": "not_found"})

        if session.is_revoked:
            raise SessionRevokedError(context={"session_id": session.session_id})

        if session.expires_at <= self._now():
            raise SessionExpiredError(context={"session_id": session.session_id})

        return session

    async def revoke_session(self, session_id: str) -> None:
        """Revoke an existing session."""
        session = await self.repo.get_by_session_id(session_id)

        if not session:
            return

        session.is_revoked = True
        session.revoked_at = self._now()
        await self.repo.save()
        logger.info("Session revoked, session_id={}", session_id)

    async def list_sessions_for_user(self, user_id: int) -> list[Session]:
        """List sessions for a user."""
        return await self.repo.list_by_user_id(user_id)

    async def revoke_all_sessions_for_user(self, user_id: int) -> int:
        """Revoke all sessions for a user. Returns number of sessions revoked."""
        sessions = await self.repo.list_by_user_id(user_id)
        if not sessions:
            return 0

        now = self._now()
        for session in sessions:
            if not session.is_revoked:
                session.is_revoked = True
                session.revoked_at = now

        await self.repo.save()
        logger.info(
            "All sessions revoked, user_id={}, count={}", user_id, len(sessions)
        )
        return len(sessions)
