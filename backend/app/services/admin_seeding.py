# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
"""Admin user seeding service.

This module provides functionality to initialize the database and seed
the default admin user on application startup.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.logging import get_logger
from app.core.settings import get_app_settings
from app.core.utils.hashing import hash_password
from app.models.mixins import Base
from app.models.users import User

logger = get_logger("service.admin_seeding")


async def create_all_tables(engine: AsyncEngine) -> None:
    """Create all database tables from SQLAlchemy models.

    Args:
        engine (AsyncEngine): Async database engine.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def seed_admin_user(session: AsyncSession) -> None:
    """Seed default admin user if it doesn't exist.

    Uses admin credentials from environment variables (AdminConfig).

    Args:
        session (AsyncSession): Async database session.
    """
    settings = get_app_settings()
    admin_config = settings.admin

    try:
        async with session.begin():
            # Check if admin user already exists
            stmt = select(User).where(User.username == admin_config.username)
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                logger.info(
                    f"Admin user '{admin_config.username}' already exists, skipping seed"
                )
                return

            # Create new admin user
            admin_user = User(
                name=admin_config.name,
                username=admin_config.username,
                email=admin_config.email,
                hashed_password=hash_password(admin_config.password.get_secret_value()),
                is_admin=True,
                is_active=True,
            )

            session.add(admin_user)
            await session.flush()
            logger.info(
                f"Admin user '{admin_config.username}' created successfully (id={admin_user.id})"
            )

    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")
        raise


async def initialize_database(engine: AsyncEngine, session: AsyncSession) -> None:
    """Initialize database tables and seed default admin user.

    This function should be called on application startup.

    Args:
        engine (AsyncEngine): Async database engine.
        session (AsyncSession): Async database session.

    Example:
        from app.database.session import database_manager

        async def startup():
            async with database_manager.session() as session:
                await initialize_database(database_manager.engine, session)
    """
    logger.info("Starting database initialization...")
    await create_all_tables(engine)
    await seed_admin_user(session)
    logger.info("Database initialization completed successfully")
