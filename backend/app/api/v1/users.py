# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""User password management endpoints."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_password_service
from app.services.auth.auth_schemas import ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user password",
)
async def change_password(
    data: ChangePasswordRequest,
    user=Depends(get_current_user),
    service=Depends(get_password_service),
) -> None:
    """Change password for the currently authenticated user."""
    await service.change_password(user, data)
