"""Tests for authentication system.

This module contains tests for JWT, password hashing, and security functions.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    create_token,
    create_token_pair,
    get_token_expiry,
    get_token_jti,
    verify_token,
)
from app.core.security import (
    generate_email_verification_token,
    generate_password_reset_token,
    hash_password,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert hashed.startswith("$argon2id")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test verifying against invalid hash."""
        result = verify_password("password", "invalid_hash")
        assert result is False


@pytest.mark.unit
class TestTokenGeneration:
    """Tests for JWT token generation."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = uuid.uuid4()
        token, expiry = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = uuid.uuid4()
        token, expiry = create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert isinstance(expiry, datetime)

    def test_create_token_pair(self):
        """Test creating token pair."""
        user_id = uuid.uuid4()
        tokens = create_token_pair(user_id)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert "expires_in" in tokens
        assert tokens["token_type"] == "Bearer"
        assert tokens["expires_in"] > 0

    def test_create_token_with_roles(self):
        """Test creating token with roles."""
        user_id = uuid.uuid4()
        roles = ["admin", "user"]
        token, _ = create_access_token(user_id, roles=roles)

        payload = verify_token(token)
        assert payload.roles == roles

    def test_create_token_with_permissions(self):
        """Test creating token with permissions."""
        user_id = uuid.uuid4()
        permissions = ["users:read", "users:write"]
        token, _ = create_access_token(user_id, permissions=permissions)

        payload = verify_token(token)
        assert payload.permissions == permissions


@pytest.mark.unit
class TestTokenVerification:
    """Tests for JWT token verification."""

    def test_verify_valid_token(self):
        """Test verifying valid token."""
        user_id = uuid.uuid4()
        token, _ = create_access_token(user_id)

        payload = verify_token(token)

        assert payload.sub == user_id
        assert payload.type == "access"

    def test_verify_token_type(self):
        """Test verifying token type."""
        user_id = uuid.uuid4()
        access_token, _ = create_access_token(user_id)
        refresh_token, _ = create_refresh_token(user_id)

        access_payload = verify_token(access_token, token_type="access")
        assert access_payload.type == "access"

        refresh_payload = verify_token(refresh_token, token_type="refresh")
        assert refresh_payload.type == "refresh"

    def test_verify_wrong_token_type(self):
        """Test verifying wrong token type."""
        from app.core.exceptions import AuthenticationException

        user_id = uuid.uuid4()
        token, _ = create_access_token(user_id)

        with pytest.raises(AuthenticationException):
            verify_token(token, token_type="refresh")

    def test_verify_expired_token(self):
        """Test verifying expired token."""
        from app.core.exceptions import AuthenticationException

        user_id = uuid.uuid4()
        # Create token that expired 1 hour ago
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token, _ = create_token(
            user_id,
            token_type="access",
            expires_delta=timedelta(minutes=-60),
        )

        with pytest.raises(AuthenticationException):
            verify_token(token)

    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        from app.core.exceptions import AuthenticationException

        with pytest.raises(AuthenticationException):
            verify_token("invalid_token")


@pytest.mark.unit
class TestTokenUtilities:
    """Tests for token utility functions."""

    def test_get_token_jti(self):
        """Test extracting JTI from token."""
        user_id = uuid.uuid4()
        token, _ = create_access_token(user_id)

        jti = get_token_jti(token)
        assert jti is not None
        assert isinstance(jti, str)

    def test_get_token_jti_invalid(self):
        """Test extracting JTI from invalid token."""
        jti = get_token_jti("invalid_token")
        assert jti is None

    def test_get_token_expiry(self):
        """Test extracting expiry from token."""
        user_id = uuid.uuid4()
        token, _ = create_access_token(user_id)

        expiry = get_token_expiry(token)
        assert expiry is not None
        assert isinstance(expiry, datetime)

    def test_get_token_expiry_invalid(self):
        """Test extracting expiry from invalid token."""
        expiry = get_token_expiry("invalid_token")
        assert expiry is None


@pytest.mark.unit
class TestTokenTimings:
    """Tests for token timing configurations."""

    def test_access_token_expiry(self):
        """Test access token expires in correct time."""
        user_id = uuid.uuid4()
        _, expiry = create_access_token(user_id)

        expected_minutes = settings.jwt_access_token_expire_minutes
        now = datetime.now(timezone.utc)
        diff = expiry - now

        # Should be approximately expected_minutes
        assert abs(diff.total_seconds() / 60 - expected_minutes) < 1

    def test_refresh_token_expiry(self):
        """Test refresh token expires in correct time."""
        user_id = uuid.uuid4()
        _, expiry = create_refresh_token(user_id)

        expected_days = settings.jwt_refresh_token_expire_days
        now = datetime.now(timezone.utc)
        diff = expiry - now

        # Should be approximately expected_days
        assert abs(diff.total_seconds() / 86400 - expected_days) < 0.1


@pytest.mark.unit
class TestVerificationTokens:
    """Tests for verification token generation."""

    def test_generate_password_reset_token(self):
        """Test generating password reset token."""
        token = generate_password_reset_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 32

    def test_generate_email_verification_token(self):
        """Test generating email verification token."""
        token = generate_email_verification_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 32

    def test_tokens_are_unique(self):
        """Test that generated tokens are unique."""
        tokens = [generate_password_reset_token() for _ in range(100)]
        assert len(set(tokens)) == 100
