# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""User Repository.

This module provides data access operations for the User entity using the Repository Pattern.
It abstracts database operations and provides a clean interface for user data access.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class UserRepository:
    """Repository for user data access.

    Using Repository Pattern to abstract database operations for user management.

    Attributes:
        db (AsyncSession): The asynchronous database session.

    Methods:
        get_by_id(user_id: int) -> User | None:
            Get user by ID.
        get_by_username(username: str) -> User | None:
            Get user by username.
        get_by_email(email: str) -> User | None:
            Get user by email.
        add(user: User) -> None:
            Add a new user to the database.
        save() -> None:
            Save changes to the database.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID.

        Args:
            user_id (int): The user ID.

        Returns:
            User | None: The user if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username (str): The username.

        Returns:
            User | None: The user if found, None otherwise.
        """
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email (str): The email address.

        Returns:
            User | None: The user if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, user: User) -> None:
        """Add a new user to the database.

        Args:
            user (User): The user entity to add.
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

    async def list_users(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> list[User]:
        """List users with pagination.

        Args:
            skip (int): Number of users to skip (for pagination).
            limit (int): Maximum number of users to return.
            include_inactive (bool): Whether to include inactive users.

        Returns:
            list[User]: List of user entities.
        """
        stmt = select(User)
        if not include_inactive:
            stmt = stmt.where(User.is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save(self) -> None:
        """Save changes to the database."""
        await self.db.commit()
