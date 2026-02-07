# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""User Management Service.

This module provides user management operations for administrators including
creating users, listing users, updating user information, and deactivating users.
"""

from app.models.users import User
from app.repositories import UserRepository
from app.services.auth.auth_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.core.utils.hashing import hash_password


class UserManagementService:
    """Service for user management operations.

    This service handles administrative user operations including creation,
    listing, updating, and deactivation of user accounts.

    Attributes:
        users (UserRepository): Repository for user data access.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, data: CreateUserRequest) -> User:
        """Create a new user account.

        Args:
            data (CreateUserRequest): User creation data including username,
                email, password, and optional admin flag.

        Returns:
            User: The created user entity.

        Raises:
            UserAlreadyExistsError: If username or email already exists.
        """
        existing_by_username = await self.user_repo.get_by_username(data.username)
        if existing_by_username:
            raise ValueError(f"Username '{data.username}' already exists")

        existing_by_email = await self.user_repo.get_by_email(data.email)
        if existing_by_email:
            raise ValueError(f"Email '{data.email}' already exists")

        user = User(
            username=data.username,
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
            is_admin=data.is_admin or False,
            is_active=True,
        )

        await self.user_repo.add(user)

        return user

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[User]:
        """List users with pagination.

        Args:
            skip (int): Number of users to skip (for pagination).
            limit (int): Maximum number of users to return.
            include_inactive (bool): Whether to include inactive users.

        Returns:
            list[User]: List of user entities.
        """
        users = await self.user_repo.list_users(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
        )
        return users

    async def get_user(self, user_id: int) -> User:
        """Get a specific user by ID.

        Args:
            user_id (int): The user ID.

        Returns:
            User: The user entity.

        Raises:
            UserNotFoundError: If user is not found.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(context={"user_id": user_id})
        return user

    async def update_user(self, user_id: int, data: UpdateUserRequest) -> User:
        """Update user information.

        Args:
            user_id (int): The user ID to update.
            data (UpdateUserRequest): Updated user information.

        Returns:
            User: The updated user entity.

        Raises:
            UserNotFoundError: If user is not found.
        """
        user = await self.get_user(user_id)

        if data.name is not None:
            user.name = data.name
        if data.email is not None:
            existing = await self.user_repo.get_by_email(data.email)
            if existing and existing.id != user_id:
                raise ValueError(f"Email '{data.email}' already exists")
            user.email = data.email
        if data.is_admin is not None:
            user.is_admin = data.is_admin

        await self.user_repo.save()

        return user

    async def deactivate_user(self, user_id: int) -> None:
        """Deactivate a user account.

        Args:
            user_id (int): The user ID to deactivate.

        Raises:
            UserNotFoundError: If user is not found.
        """
        user = await self.get_user(user_id)
        user.is_active = False
        await self.user_repo.save()

    async def activate_user(self, user_id: int) -> None:
        """Activate a user account.

        Args:
            user_id (int): The user ID to activate.

        Raises:
            UserNotFoundError: If user is not found.
        """
        user = await self.get_user(user_id)
        user.is_active = True
        await self.user_repo.save()

    async def delete_user(self, user_id: int) -> None:
        """Delete a user account (soft delete via deactivation).

        Args:
            user_id (int): The user ID to delete.

        Raises:
            UserNotFoundError: If user is not found.
        """
        await self.deactivate_user(user_id)
