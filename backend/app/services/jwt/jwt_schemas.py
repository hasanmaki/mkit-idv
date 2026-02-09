# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.


"""Pydantic schemas for JWT service.

IMPORTANT: This module defines only cryptographic and token-level claims for JWTs.
Business logic claims (is_admin, is_active, roles, permissions, etc.) MUST NOT be included here.
JWTService is responsible only for signing, verifying, and validating token structure and cryptographic claims.
Authorization and user/session state checks belong in SessionService/UserService/AuthService.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class AccessTokenPayload(BaseModel):
    """Payload for JWT access token.

    Attributes:
        sub (str): Subject (user ID) as string.
        jti (str): JWT ID (session ID).
        type (str): Token type identifier.
        iat (datetime): Issued at timestamp.
        exp (datetime): Expiration timestamp.
    """

    sub: str = Field(..., description="Subject (user ID)")
    jti: str = Field(..., description="JWT ID (session ID)")
    type: str = Field(default="access", description="Token type")
    iat: datetime = Field(..., description="Issued at timestamp")
    exp: datetime = Field(..., description="Expiration timestamp")

    model_config = {
        "json_encoders": {datetime: lambda v: v.timestamp()},
        "extra": "allow",
    }

    @property
    def user_id(self) -> int:
        """Get user ID from subject claim."""
        return int(self.sub)

    @property
    def session_id(self) -> str:
        """Get session ID from JWT ID claim."""
        return self.jti
