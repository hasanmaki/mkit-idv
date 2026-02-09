# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

# ruff : noqa : B904
# [ ] TODO : Fix Later About Docstring
"""This service is responsible for JWT implementation.

IMPORTANT: This service is a cryptographic boundary. It MUST NOT encode or check business logic claims (is_admin, is_active, roles, permissions, etc.).
It is only responsible for signing, verifying, and validating token structure and cryptographic claims (sub, jti, iat, exp, type, aud, iss, etc.).
Authorization and user/session state checks belong in SessionService/UserService/AuthService.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as PyJwtInvalidTokenError

from app.core.logging import get_logger
from app.core.settings import JwtConfig

from .jwt_errors import (
    JwtExpiredTokenError,
    JwtInvalidTokenError,
    JwtInvalidTokenTypeError,
    JwtMissingClaimError,
)
from .jwt_schemas import AccessTokenPayload

logger = get_logger("service.jwt")


class JwtService:
    """Service for creating and verifying JWT tokens.

    Attributes:
        ACCESS_TOKEN_TYPE (str): Constant for access token type.

    Methods:
        create_access_token: Create a new access token.
        verify_access_token: Verify an access token.
        generate_refresh_token: Generate an opaque refresh token (plaintext + hash).
        hash_refresh_token: Hash an opaque refresh token.

    Usage:
        config = JwtConfig(...)
        jwt_service = JwtService(config)
        access_token = jwt_service.create_access_token(user_id=1, session_id="...")
        payload = jwt_service.verify_access_token(access_token)
        refresh_token, refresh_hash = jwt_service.generate_refresh_token()

    """

    ACCESS_TOKEN_TYPE = "access"

    def __init__(self, config: JwtConfig) -> None:
        self._secret: str = config.secret
        self._algorithm: str = config.algorithm
        self._access_exp_minutes: int = config.access_token_expire_minutes

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
                options={"verify_aud": False},
            )
        except ExpiredSignatureError as exc:
            logger.debug("Token verification failed: {}", exc.__class__.__name__)
            raise JwtExpiredTokenError(original_exception=exc)
        except PyJwtInvalidTokenError as exc:
            logger.debug("Token verification failed: {}", exc.__class__.__name__)
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
        now = self._now()
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "jti": session_id,
            "type": self.ACCESS_TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(minutes=self._access_exp_minutes),
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
                raise ValueError(f"Forbidden claims: {overlap}")
            payload.update(extra_claims)

        payload_model = AccessTokenPayload(**payload)
        token = self._encode(payload_model.model_dump())
        logger.debug(
            "Access token created, user_id={}, session_id={}", user_id, session_id
        )
        return token

    def verify_access_token(self, token: str) -> AccessTokenPayload:
        """Verify an access token.

        Args:
            token (str): The JWT access token to verify.

        Returns:
            AccessTokenPayload: The decoded and validated token payload.

        Raises:
            JwtExpiredTokenError: If the token has expired.
            JwtInvalidTokenError: If the token is invalid or signature is wrong.
            JwtInvalidTokenTypeError: If the token type is not "access".
            JwtMissingClaimError: If required claims are missing.
        """
        payload = self._decode_raw(token)

        token_type = self._require_claim(payload, "type")
        if token_type != self.ACCESS_TOKEN_TYPE:
            logger.debug(
                "Invalid token type: expected={}, actual={}",
                self.ACCESS_TOKEN_TYPE,
                token_type,
            )
            raise JwtInvalidTokenTypeError(
                context={"expected": self.ACCESS_TOKEN_TYPE, "actual": token_type}
            )

        self._require_claim(payload, "sub")
        self._require_claim(payload, "jti")

        return AccessTokenPayload(**payload)

    def generate_refresh_token(self) -> tuple[str, str]:
        """Generate an opaque refresh token.

        Returns:
            tuple[str, str]: A tuple containing (plaintext_token, hashed_token).
            The plaintext token is returned to the client.
            The hashed token is stored in the database.
        """
        token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash

    def hash_refresh_token(self, token: str) -> str:
        """Hash an opaque refresh token.

        Args:
            token (str): The plaintext refresh token.

        Returns:
            str: The SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()
