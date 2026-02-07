# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Authentication Schemas.

This module defines Pydantic schemas for authentication operations including
login, token refresh, and token responses.
"""

from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    """Schema for login response containing both tokens.

    Attributes:
        access_token (str): The JWT access token for API authentication.
        refresh_token (str): The opaque refresh token for obtaining new access tokens.
        token_type (str): Token type (bearer).
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Opaque refresh token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIs...",
                    "refresh_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ",
                    "token_type": "bearer",
                }
            ]
        }
    }


class RefreshTokenResponse(BaseModel):
    """Schema for token refresh response.

    Attributes:
        access_token (str): The new JWT access token.
        refresh_token (str): The new opaque refresh token (optional, may be rotated).
    """

    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New opaque refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIs...",
                    "refresh_token": "xYzWvUtSrQpOnMlKjIhGfEdCbA",
                }
            ]
        }
    }


class RefreshTokenInput(BaseModel):
    """Schema for token refresh input.

    Attributes:
        refresh_token (str): The opaque refresh token.
    """

    refresh_token: str = Field(..., description="Opaque refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [{"refresh_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ"}]
        }
    }


class LogoutInput(BaseModel):
    """Schema for logout input.

    Attributes:
        refresh_token (str): The opaque refresh token to revoke.
    """

    refresh_token: str = Field(..., description="Opaque refresh token to revoke")

    model_config = {
        "json_schema_extra": {
            "examples": [{"refresh_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ"}]
        }
    }


class AdminRevokeSessionInput(BaseModel):
    """Schema for admin revoke a specific session."""

    session_id: str = Field(..., description="Session ID to revoke")


class AdminRevokeUserSessionsInput(BaseModel):
    """Schema for admin revoke all sessions of a user."""

    user_id: int = Field(..., description="User ID")


class CurrentUserResponse(BaseModel):
    """Schema for current user response."""

    id: int
    name: str
    username: str
    email: str
    is_admin: bool
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class CreateUserRequest(BaseModel):
    """Schema for creating a new user (admin only)."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="Full name")
    password: str = Field(
        ..., min_length=12, description="Password (min 12 characters)"
    )
    is_admin: bool = Field(default=False, description="Admin privileges")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "name": "John Doe",
                    "password": "SecurePassword123!",
                    "is_admin": False,
                }
            ]
        }
    }


class UpdateUserRequest(BaseModel):
    """Schema for updating user information (admin only)."""

    name: str | None = Field(None, description="Full name")
    email: str | None = Field(None, description="Email address")
    is_admin: bool | None = Field(None, description="Admin privileges")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Smith",
                    "email": "john.smith@example.com",
                    "is_admin": True,
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    email: str
    name: str
    is_admin: bool
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class UserPublic(BaseModel):
    """Schema for public user information."""

    id: int
    username: str
    name: str

    model_config = {
        "from_attributes": True,
    }


class ChangePasswordRequest(BaseModel):
    """Schema for user password change."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=12, description="New password (min 12 characters)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_password": "OldPassword123!",
                    "new_password": "NewSecurePassword456!",
                }
            ]
        }
    }


class ResetPasswordRequest(BaseModel):
    """Schema for admin password reset."""

    new_password: str = Field(
        ..., min_length=12, description="New password (min 12 characters)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "new_password": "AdminResetPassword123!",
                }
            ]
        }
    }
