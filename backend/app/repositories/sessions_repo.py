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

from app.models.sessions import Session


class SessionRepository:
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
        self.db = db

    async def get_by_session_id(self, session_id: str) -> Session | None:
        """Get session by session_id."""
        stmt = select(Session).where(Session.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, session: Session) -> None:
        """Add a new session to the database."""
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

    async def save(self) -> None:
        """Save changes to the database."""
        await self.db.commit()
