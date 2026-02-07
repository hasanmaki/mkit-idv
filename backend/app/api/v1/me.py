# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""Current user endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.services.auth.auth_schemas import CurrentUserResponse

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
