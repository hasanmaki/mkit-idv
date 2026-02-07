# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""Password Service.

This module provides password-related operations including password change
for users and password reset by administrators.
"""

from app.models.users import User
from app.repositories import UserRepository
from app.services.auth.auth_errors import InvalidCredentialsError, UserNotFoundError
from app.services.auth.auth_schemas import ChangePasswordRequest, ResetPasswordRequest
from app.core.utils.hashing import hash_password, verify_password


class PasswordService:
    """Service for password-related operations.

    This service handles password changes by users and password resets
    by administrators.

    Attributes:
        users (UserRepository): Repository for user data access.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Change password for the current user.

        Args:
            user (User): The user whose password to change.
            data (ChangePasswordRequest): Password change data containing
                current password and new password.

        Raises:
            InvalidCredentialsError: If current password is incorrect.
            ValueError: If new password is the same as current password.
        """
        if not verify_password(data.current_password, user.hashed_password):
            raise InvalidCredentialsError()

        if verify_password(data.new_password, user.hashed_password):
            raise ValueError("New password must be different from current password")

        if len(data.new_password) < 12:
            raise ValueError("Password must be at least 12 characters long")

        user.hashed_password = hash_password(data.new_password)
        await self.user_repo.save()

    async def reset_password_by_admin(
        self,
        user_id: int,
        data: ResetPasswordRequest,
    ) -> None:
        """Reset user password (admin operation).

        Args:
            user_id (int): The user ID whose password to reset.
            data (ResetPasswordRequest): New password data.

        Raises:
            UserNotFoundError: If user is not found.
            ValueError: If new password is too short.
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundError(context={"user_id": user_id})

        if len(data.new_password) < 12:
            raise ValueError("Password must be at least 12 characters long")

        user.hashed_password = hash_password(data.new_password)
        await self.user_repo.save()
