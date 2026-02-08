# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""Current user endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_password_service
from app.services.auth.auth_schemas import ChangePasswordRequest, CurrentUserResponse

router = APIRouter(tags=["Users"])


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
)
async def get_me(user=Depends(get_current_user)) -> CurrentUserResponse:
    """Return current user info."""
    return CurrentUserResponse.model_validate(user)


@router.post(
    "/me/change-password",
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
