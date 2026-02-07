# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""About Exceptions Of JWT.

Note:
    - Important constraints or considerations
"""

from app.core.exceptions import AppBaseExceptionError


class JwtError(AppBaseExceptionError):
    """Base class for JWT-related errors."""

    DEFAULT_MESSAGE = "Token tidak valid."
    DEFAULT_STATUS_CODE = 401
    DEFAULT_CODE = "jwt_error"
    DEFAULT_LOG_LEVEL = "WARNING"


class JwtInvalidTokenError(JwtError):
    """JWT cannot be decoded or signature is invalid."""

    DEFAULT_MESSAGE = "Token tidak valid atau rusak."
    DEFAULT_CODE = "jwt_invalid"


class JwtExpiredTokenError(JwtError):
    """JWT is expired."""

    DEFAULT_MESSAGE = "Token sudah kedaluwarsa."
    DEFAULT_CODE = "jwt_expired"


class JwtInvalidTokenTypeError(JwtError):
    """JWT type mismatch (access vs refresh)."""

    DEFAULT_MESSAGE = "Tipe token tidak valid."
    DEFAULT_CODE = "jwt_invalid_type"


class JwtMissingClaimError(JwtError):
    """Required JWT claim is missing."""

    DEFAULT_MESSAGE = "Token tidak memiliki klaim yang diperlukan."
    DEFAULT_CODE = "jwt_missing_claim"
