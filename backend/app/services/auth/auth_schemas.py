# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Authentication Schemas.

This module defines Pydantic schemas for authentication operations including
login, token refresh, and token responses.
"""

from pydantic import BaseModel, Field


class LoginInput(BaseModel):
    """Schema for user login input.

    Attributes:
        username (str): The username or email of the user.
        password (str): The user's password.
    """

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "examples": [{"username": "john_doe", "password": "secret123"}]
        }
    }


class LoginResponse(BaseModel):
    """Schema for login response containing both tokens.

    Attributes:
        access_token (str): The JWT access token for API authentication.
        refresh_token (str): The opaque refresh token for obtaining new access tokens.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Opaque refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIs...",
                    "refresh_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ",
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
