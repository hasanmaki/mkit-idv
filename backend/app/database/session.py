# Copyright (c) 2025 Hasan Maki. All rights reserved.
"""Database session module for application.

This module provides database connection and session management functionality
for the application using SQLAlchemy.

Note:
    This module uses SQLite with aiosqlite driver by default.
"""

import contextlib
from collections.abc import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.logging import get_logger
from app.core.settings import get_app_settings
from app.database.db_errors import (
    DatabaseInternalError,
    DatabaseUnavailableError,
)

logger = get_logger("db")


class DatabaseSessionManager:
    """Database session manager for handling connections and sessions.

    Args:
        host (str): Database connection string.
    """

    def __init__(self, host: str):
        self.engine: AsyncEngine | None = create_async_engine(
            host, pool_pre_ping=True
        )
        self._sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            expire_on_commit=False,
        )

    async def close(self):
        """Close the database engine and sessionmaker."""
        if self.engine is None:
            logger.warning("Database engine already closed")
            return
        await self.engine.dispose()
        self.engine = None
        self._sessionmaker = None  # type: ignore

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Get connection from the pool."""
        if self.engine is None:
            raise DatabaseUnavailableError(
                message="Mesin database belum diinisialisasi.",
                error_code="db_engine_not_initialized",
            )

        async with self.engine.begin() as connection:
            try:
                yield connection
            except SQLAlchemyError as e:
                logger.error("Connection error occurred: {}", e)
                raise DatabaseUnavailableError(
                    message="Koneksi database gagal.",
                    error_code="db_connection_failed",
                    original_exception=e,
                ) from e

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Get session from the sessionmaker."""
        if not self._sessionmaker:
            logger.error("Sessionmaker is not available")
            raise DatabaseUnavailableError(
                message="Session database tidak tersedia.",
                error_code="db_session_unavailable",
            )

        session = self._sessionmaker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error("Session error occurred: {}", e)
            raise DatabaseInternalError(
                message="Terjadi kesalahan pada session database.",
                error_code="db_session_error",
                original_exception=e,
            ) from e
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(get_app_settings().db.db_url)
# singleton instance


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Dependency inject session + auto commit/rollback."""
    async with sessionmanager.session() as session:
        try:
            yield session
            await session.commit()
            logger.debug("Database session committed successfully")
        except BaseException:
            await session.rollback()
            logger.warning("Database session rolled back due to error")
            raise
