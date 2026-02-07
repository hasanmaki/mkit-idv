# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""User management endpoints (admin only)."""

from fastapi import APIRouter, Depends, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import require_admin
from app.repositories import UserRepository
from app.services.auth.auth_schemas import (
    CreateUserRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.services.password import PasswordService
from app.services.user_management import UserManagementService

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])
limiter = Limiter(key_func=get_remote_address)


def get_user_management_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserManagementService:
    """Dependency for UserManagementService."""
    return UserManagementService(user_repo)


def get_password_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> PasswordService:
    """Dependency for PasswordService."""
    return PasswordService(user_repo)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    data: CreateUserRequest,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Create a new user account (admin only)."""
    user = await service.create_user(data)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = await service.list_users(
        skip=skip, limit=limit, include_inactive=include_inactive
    )
    return [UserResponse.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
)
async def get_user(
    user_id: int,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Get a specific user by ID (admin only)."""
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
)
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Update user information (admin only)."""
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user",
)
async def deactivate_user(
    user_id: int,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> None:
    """Deactivate a user account (admin only)."""
    await service.deactivate_user(user_id)


@router.post(
    "/{user_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Activate user",
)
async def activate_user(
    user_id: int,
    admin=Depends(lambda: get_current_user),
    service: UserManagementService = Depends(get_user_management_service),
) -> None:
    """Activate a user account (admin only)."""
    await service.activate_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    data: CreateUserRequest,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Create a new user account (admin only)."""
    user = await service.create_user(data)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = await service.list_users(
        skip=skip, limit=limit, include_inactive=include_inactive
    )
    return [UserResponse.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
)
async def get_user(
    user_id: int,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Get a specific user by ID (admin only)."""
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
)
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserResponse:
    """Update user information (admin only)."""
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user",
)
async def deactivate_user(
    user_id: int,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> None:
    """Deactivate a user account (admin only)."""
    await service.deactivate_user(user_id)


@router.post(
    "/{user_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Activate user",
)
async def activate_user(
    user_id: int,
    admin=Depends(require_admin),
    service: UserManagementService = Depends(get_user_management_service),
) -> None:
    """Activate a user account (admin only)."""
    await service.activate_user(user_id)


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset user password",
)
async def reset_password(
    user_id: int,
    data: ResetPasswordRequest,
    admin=Depends(require_admin),
    service: PasswordService = Depends(get_password_service),
) -> None:
    """Reset user password (admin only)."""
    await service.reset_password_by_admin(user_id, data)
