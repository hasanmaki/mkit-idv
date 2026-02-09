# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.

"""
Tests for JWT service.

IMPORTANT: These tests enforce the cryptographic boundary of the JWT service.
Business logic claims (is_admin, is_active, roles, permissions, etc.) MUST NOT be included in JWT payloads or tested here.
JWTService is responsible only for signing, verifying, and validating token structure and cryptographic claims (sub, jti, iat, exp, type, etc.).
Authorization and user/session state checks belong in SessionService/UserService/AuthService and should be tested separately.
"""

from datetime import UTC, datetime, timedelta

import pytest
from app.core.settings import JwtConfig
from app.services.jwt import (
    AccessTokenPayload,
    JwtExpiredTokenError,
    JwtInvalidTokenError,
    JwtInvalidTokenTypeError,
    JwtService,
)
from faker import Faker
from pydantic import SecretStr


@pytest.fixture
def faker() -> Faker:
    """Faker fixture for generating test data."""
    return Faker()


@pytest.fixture
def jwt_config() -> JwtConfig:
    """JWT configuration fixture for testing."""

    return JwtConfig(
        secret_key=SecretStr("test-secret-key-for-testing-only"),
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_minutes=1440,  # 24 hours
    )


@pytest.fixture
def jwt_service(jwt_config: JwtConfig) -> JwtService:
    """JWT service fixture."""
    return JwtService(jwt_config)


class TestJwtServiceInit:
    """Tests for JwtService initialization."""

    def test_init_with_config(self, jwt_config: JwtConfig) -> None:
        """Test that JwtService initializes with correct config."""
        service = JwtService(jwt_config)
        assert service._secret == jwt_config.secret
        assert service._algorithm == jwt_config.algorithm
        assert service._access_exp_minutes == jwt_config.access_token_expire_minutes


class TestCreateAccessToken:
    """Tests for access token creation."""

    def test_create_access_token_basic(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test basic access token creation."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

    def test_create_access_token_with_forbidden_extra_claims(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test that forbidden business claims in extra_claims raise ValueError."""
        user_id = faker.random_int()
        session_id = faker.uuid4()
        forbidden_claims = [
            {"role": "admin"},
            {"is_admin": True},
            {"is_active": True},
            {"permissions": ["read"]},
        ]
        for claims in forbidden_claims:
            with pytest.raises(ValueError):
                jwt_service.create_access_token(
                    user_id=user_id, session_id=session_id, extra_claims=claims
                )

    def test_create_access_token_with_allowed_extra_claims(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test access token creation with allowed extra claims (custom, non-privileged, non-sensitive)."""
        user_id = faker.random_int()
        session_id = faker.uuid4()
        extra_claims = {"custom": "value", "foo": 123}
        token = jwt_service.create_access_token(
            user_id=user_id, session_id=session_id, extra_claims=extra_claims
        )
        payload = jwt_service.verify_access_token(token)
        assert payload.model_dump().get("custom") == "value"
        assert payload.model_dump().get("foo") == 123

    def test_create_access_token_without_extra_claims(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test access token creation without extra claims."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)

        payload = jwt_service.verify_access_token(token)
        assert payload.sub == str(user_id)
        assert payload.jti == session_id
        assert payload.type == "access"


class TestRefreshTokenGeneration:
    """Tests for opaque refresh token generation and hashing."""

    def test_generate_refresh_token_basic(self, jwt_service: JwtService) -> None:
        """Test basic refresh token generation."""
        token, token_hash = jwt_service.generate_refresh_token()
        assert isinstance(token, str)
        assert isinstance(token_hash, str)
        assert token != token_hash
        assert len(token) > 32

    def test_hash_refresh_token_matches_generated_hash(
        self, jwt_service: JwtService
    ) -> None:
        """Test that hashing a token matches the generated hash."""
        token, token_hash = jwt_service.generate_refresh_token()
        assert jwt_service.hash_refresh_token(token) == token_hash

    def test_hash_refresh_token_is_stable(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test that refresh token hashing is deterministic."""
        token = faker.sha256()
        assert jwt_service.hash_refresh_token(token) == jwt_service.hash_refresh_token(
            token
        )


class TestVerifyAccessToken:
    """Tests for access token verification."""

    def test_verify_access_token_success(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test successful access token verification."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)
        payload = jwt_service.verify_access_token(token)

        assert isinstance(payload, AccessTokenPayload)
        assert payload.user_id == user_id
        assert payload.session_id == session_id
        assert payload.type == "access"

    def test_verify_access_token_returns_pydantic_model(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test that verify_access_token returns a Pydantic model."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)
        payload = jwt_service.verify_access_token(token)

        # Test that it's a Pydantic model with model_dump method
        assert hasattr(payload, "model_dump")
        assert hasattr(payload, "model_dump_json")

    def test_verify_access_token_invalid_token(self, jwt_service: JwtService) -> None:
        """Test verification with invalid token."""
        with pytest.raises(JwtInvalidTokenError):
            jwt_service.verify_access_token("invalid.token.string")

    def test_verify_access_token_expired_token(
        self, jwt_service: JwtService, faker: Faker, monkeypatch
    ) -> None:
        """Test verification with expired token."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        # Mock _now to return a time in the past
        past_time = datetime.now(UTC) - timedelta(hours=2)
        monkeypatch.setattr(jwt_service, "_now", lambda: past_time)

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)

        # Restore _now to current time for verification
        monkeypatch.undo()

        with pytest.raises(JwtExpiredTokenError):
            jwt_service.verify_access_token(token)

    def test_verify_access_token_wrong_type(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test verification with wrong token type."""
        user_id = faker.random_int()
        session_id = faker.uuid4()
        token = jwt_service._encode(  # pyright: ignore[reportPrivateUsage]
            {
                "sub": str(user_id),
                "jti": session_id,
                "type": "refresh",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=30),
            }
        )

        with pytest.raises(JwtInvalidTokenTypeError) as exc_info:
            jwt_service.verify_access_token(token)

        assert "expected" in exc_info.value.context
        assert exc_info.value.context["expected"] == "access"
        assert exc_info.value.context["actual"] == "refresh"


class TestTokenExpiration:
    """Tests for token expiration."""

    def test_access_token_expiration_time(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test that access token has correct expiration time."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        now = datetime.now(UTC)
        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)
        payload = jwt_service.verify_access_token(token)

        # Check that expiration is approximately 30 minutes from now
        expected_exp = now + timedelta(minutes=30)
        time_diff = abs((payload.exp - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 seconds tolerance


class TestAccessTokenPayload:
    """Tests for AccessTokenPayload Pydantic model."""

    def test_access_token_payload_properties(self, faker: Faker) -> None:
        """Test AccessTokenPayload properties."""
        user_id = faker.random_int()
        session_id = faker.uuid4()
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)

        payload = AccessTokenPayload(
            sub=str(user_id),
            jti=session_id,
            type="access",
            iat=now,
            exp=exp,
        )

        assert payload.user_id == user_id
        assert payload.session_id == session_id

    def test_access_token_payload_validation(self) -> None:
        """Test that AccessTokenPayload validates required fields."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)

        # Missing required field should raise validation error
        with pytest.raises(ValueError):  # Pydantic validation error
            AccessTokenPayload(
                sub="123",
                jti="session-123",
                type="access",
                iat=now,
                # exp is missing
            )  # pyright: ignore[reportCallIssue]


class TestTokenClaims:
    """Tests for token claims."""

    def test_access_token_has_required_claims(
        self, jwt_service: JwtService, faker: Faker
    ) -> None:
        """Test that access token has all required claims."""
        user_id = faker.random_int()
        session_id = faker.uuid4()

        token = jwt_service.create_access_token(user_id=user_id, session_id=session_id)
        payload = jwt_service.verify_access_token(token)

        assert hasattr(payload, "sub")
        assert hasattr(payload, "jti")
        assert hasattr(payload, "type")
        assert hasattr(payload, "iat")
        assert hasattr(payload, "exp")


class TestTokenTypes:
    """Tests for token type constants."""

    def test_access_token_type_constant(self, jwt_service: JwtService) -> None:
        """Test access token type constant."""
        assert jwt_service.ACCESS_TOKEN_TYPE == "access"
