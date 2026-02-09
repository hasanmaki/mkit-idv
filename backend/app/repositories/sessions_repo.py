# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""this module is repository.

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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.sessions import Session
from app.repositories.base_repo import BaseRepository
from app.services.sessions.session_schemas import SessionCreate, SessionUpdate

logger = get_logger("repo.sessions")


class SessionRepository(BaseRepository[Session, SessionCreate, SessionUpdate]):
    """Repository for session data access.

    using Repository Pattern  to abstract database operations for session management.

    Attributes:
        db (AsyncSession): The asynchronous database session.

    Methods:
        get_by_session_id(session_id: str) -> Session | None:
            Get session by session_id.
        add(session: Session) -> None:
            Add a new session to the database.
        save() -> None:
            Save changes to the database.

    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, Session)

    async def get_by_session_id(self, session_id: str) -> Session | None:
        """Get session by session_id."""
        stmt = select(Session).where(Session.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, session: Session) -> None:
        """Add a new session to the database."""
        await super().add(session)
        logger.debug("Session persisted, session_id={}", session.session_id)

    async def get_by_refresh_token_hash(
        self, refresh_token_hash: str
    ) -> Session | None:
        """Get session by refresh token hash."""
        stmt = select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Session]:
        """List sessions by user id."""
        stmt = select(Session).where(Session.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save(self) -> None:
        """Flush pending changes to the database."""
        await super().save()
        logger.debug("Session repository changes flushed")
