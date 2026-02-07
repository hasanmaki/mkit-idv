# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

# ruff : noqa : B904
# [ ] TODO : Fix Later About Docstring
"""This service is responsible for JWT implementation.

IMPORTANT: This service is a cryptographic boundary. It MUST NOT encode or check business logic claims (is_admin, is_active, roles, permissions, etc.).
It is only responsible for signing, verifying, and validating token structure and cryptographic claims (sub, jti, iat, exp, type, aud, iss, etc.).
Authorization and user/session state checks belong in SessionService/UserService/AuthService.
"""

# services/auth/jwt_services.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as PyJwtInvalidTokenError

from app.core.settings import JwtConfig

from .jwt_errors import (
    JwtExpiredTokenError,
    JwtInvalidTokenError,
    JwtInvalidTokenTypeError,
    JwtMissingClaimError,
)
from .jwt_schemas import (
    AccessTokenPayload,
    RefreshTokenPayload,
)


class JwtService:
    """Service for creating and verifying JWT tokens.

    Attributes:
        ACCESS_TOKEN_TYPE (str): Constant for access token type.
        REFRESH_TOKEN_TYPE (str): Constant for refresh token type.

    Methods:
        create_access_token: Create a new access token.
        create_refresh_token: Create a new refresh token.
        verify_access_token: Verify an access token.
        verify_refresh_token: Verify a refresh token.

    Usage:
        config = JwtConfig(...)
        jwt_service = JwtService(config)
        access_token = jwt_service.create_access_token(user_id=1, session_id="...")
        payload = jwt_service.verify_access_token(access_token)

    """

    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    def __init__(self, config: JwtConfig) -> None:
        self._secret: str = config.secret
        self._algorithm: str = config.algorithm
        self._access_exp_minutes: int = config.access_token_expire_minutes
        self._refresh_exp_minutes: int = config.refresh_token_expire_minutes

    def _now(self) -> datetime:
        """Separated for testability."""
        return datetime.now(UTC)

    def _encode(self, payload: dict[str, Any]) -> str:
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def _decode_raw(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except ExpiredSignatureError as exc:
            raise JwtExpiredTokenError(original_exception=exc)
        except PyJwtInvalidTokenError as exc:
            raise JwtInvalidTokenError(original_exception=exc)

    def _require_claim(self, payload: dict[str, Any], key: str) -> Any:
        if key not in payload:
            raise JwtMissingClaimError(context={"missing_claim": key})
        return payload[key]

    def create_access_token(
        self,
        *,
        user_id: int,
        session_id: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a new access token.

        Args:
            user_id (int): ID of the user.
            session_id (str): ID of the session.
            extra_claims (dict[str, Any] | None): Additional immutable, non-privileged claims (e.g., aud, iss). Business claims are forbidden.

        Returns:
            str: Encoded JWT access token.

        Raises:
            ValueError: If forbidden business claims are present in extra_claims.
        """
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "jti": session_id,
            "type": self.ACCESS_TOKEN_TYPE,
            "iat": self._now(),
            "exp": self._now() + timedelta(minutes=self._access_exp_minutes),
        }

        if extra_claims:
            forbidden = {
                "is_admin",
                "is_active",
                "role",
                "roles",
                "permission",
                "permissions",
            }
            overlap = forbidden.intersection(extra_claims.keys())
            if overlap:
                raise ValueError(
                    f"Forbidden business claims in extra_claims: {overlap}"
                )
            payload.update(extra_claims)

        return self._encode(payload)

    def create_refresh_token(
        self,
        *,
        session_id: str,
    ) -> str:
        """Create a new refresh token.

        Args:
            session_id (str): ID of the session.

        Returns:
            str: Encoded JWT refresh token.

        """
        payload: dict[str, Any] = {
            "jti": session_id,
            "type": self.REFRESH_TOKEN_TYPE,
            "iat": self._now(),
            "exp": self._now() + timedelta(minutes=self._refresh_exp_minutes),
        }

        return self._encode(payload)

    # -------------------------
    # Verification
    # -------------------------

    def verify_access_token(self, token: str) -> AccessTokenPayload:
        """Verify an access token.

        Args:
            token (str): Encoded JWT access token.

        Returns:
            AccessTokenPayload: Validated token payload.

        Raises:
            JwtExpiredTokenError: If token is expired.
            JwtInvalidTokenError: If token is invalid.
            JwtInvalidTokenTypeError: If token is not an access token.
            JwtMissingClaimError: If required claims are missing.
        """
        payload = self._decode_raw(token)

        token_type = self._require_claim(payload, "type")
        if token_type != self.ACCESS_TOKEN_TYPE:
            raise JwtInvalidTokenTypeError(
                context={"expected": self.ACCESS_TOKEN_TYPE, "actual": token_type}
            )

        self._require_claim(payload, "sub")
        self._require_claim(payload, "jti")

        return AccessTokenPayload(**payload)

    def verify_refresh_token(self, token: str) -> RefreshTokenPayload:
        """Verify a refresh token.

        Args:
            token (str): Encoded JWT refresh token.

        Returns:
            RefreshTokenPayload: Validated token payload.

        Raises:
            JwtExpiredTokenError: If token is expired.
            JwtInvalidTokenError: If token is invalid.
            JwtInvalidTokenTypeError: If token is not a refresh token.
            JwtMissingClaimError: If required claims are missing.
        """
        payload = self._decode_raw(token)

        token_type = self._require_claim(payload, "type")
        if token_type != self.REFRESH_TOKEN_TYPE:
            raise JwtInvalidTokenTypeError(
                context={"expected": self.REFRESH_TOKEN_TYPE, "actual": token_type}
            )

        self._require_claim(payload, "jti")

        return RefreshTokenPayload(**payload)
