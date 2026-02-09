# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""server repositories.

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
from app.models.apiservers import Servers
from app.repositories.base_repo import BaseRepository
from app.services.servers.server_schemas import ServerCreate, ServerUpdate

logger = get_logger("repo.servers")


class ServerRepository(BaseRepository[Servers, ServerCreate, ServerUpdate]):
    """Repository for server data access.

    using Repository Pattern  to abstract database operations for server management.

    Attributes:
        db (AsyncSession): The asynchronous database session.

    Methods:
        add(server: Servers) -> None:
            Add a new server to the database.
        save() -> None:
            Save changes to the database.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, Servers)

    async def get_by_server_id(self, server_id: int) -> Servers | None:
        """Get server by ID."""
        return await super().get_by_id(server_id)

    async def get_by_name(self, name: str) -> Servers | None:
        """Get server by name."""
        stmt = select(Servers).where(Servers.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_id(self, server_id: int, **kwargs) -> None:
        """Update server by ID."""
        server = await super().get_by_id(server_id)
        if server:
            await self.update(server, kwargs)
            logger.debug("Server updated, server_id={}", server_id)

    async def list_servers(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> list[Servers]:
        """List servers with pagination.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            include_inactive (bool): Whether to include inactive servers.

        Returns:
            list[Servers]: List of servers.

        """
        stmt = select(Servers)
        if not include_inactive:
            stmt = stmt.where(Servers.is_active.is_(True))
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete_by_id(self, server_id: int) -> None:
        """Soft delete server by ID.

        Args:
            server_id (int): The ID of the server to soft delete.

        Returns:
            None
        """
        server = await super().get_by_id(server_id)
        if server:
            await self.update(server, {"is_active": False})
            logger.debug("Server soft-deleted, server_id={}", server_id)

    async def add(self, server: "Servers") -> None:
        """Add a new server to the database.

        Args:
            server (Servers): The server entity to add.
        """
        await super().add(server)
        logger.debug("Server persisted, server_id={}", server.id)

    async def save(self) -> None:
        """Flush pending changes to the database."""
        await super().save()
