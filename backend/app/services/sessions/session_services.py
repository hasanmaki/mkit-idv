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

from app.models.sessions import Session
from app.repositories import SessionRepository
from app.services.sessions.session_errors import (
    RefreshTokenMismatchError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError,
)
from app.services.sessions.session_schemas import SessionCreate, SessionValidationResult


class SessionService:
    """Business logic for session lifecycle."""

    def __init__(self, repo: SessionRepository):
        self.repo = repo

    def _now(self) -> datetime:
        return datetime.now(UTC)

    async def create_session(self, data: SessionCreate) -> Session:
        """Create a new session."""
        session = Session(
            user_id=data.user_id,
            session_id=data.session_id,
            refresh_token_hash=data.refresh_token_hash,
            expires_at=data.expires_at,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
        )
        await self.repo.add(session)
        return session

    async def validate_session(self, session_id: str) -> SessionValidationResult:
        """Validate an existing session."""
        session = await self.repo.get_by_session_id(session_id)

        if not session:
            raise SessionNotFoundError(context={"session_id": session_id})

        if session.is_revoked:
            raise SessionRevokedError(
                context={"session_id": session_id, "revoked_at": session.revoked_at}
            )

        if session.expires_at <= self._now():
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

        if session.refresh_token_hash != refresh_token_hash:
            raise RefreshTokenMismatchError(context={"session_id": session_id})

        return session

    async def revoke_session(self, session_id: str) -> None:
        """Revoke an existing session."""
        session = await self.repo.get_by_session_id(session_id)

        if not session:
            return

        session.is_revoked = True
        session.revoked_at = self._now()
        await self.repo.save()
