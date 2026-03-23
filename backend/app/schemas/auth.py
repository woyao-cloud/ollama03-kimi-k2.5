"""Authentication Pydantic schemas.

This module defines schemas for authentication-related operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.config import settings
from app.schemas.base import BaseResponse, BaseSchema


class LoginRequest(BaseSchema):
    """Schema for user login request."""

    username: str | None = Field(
        None,
        description="Username or email address",
        examples=["johndoe"],
    )
    email: EmailStr | None = Field(
        None,
        description="Email address (alternative to username)",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePassword123!"],
    )

    @field_validator("username", "email")
    @classmethod
    def validate_credentials(cls, v: str | None, info) -> str | None:
        """Validate that either username or email is provided."""
        if info.field_name == "email" and v is None:
            # Check if username is provided
            return v
        return v


class TokenPayload(BaseSchema):
    """Schema for JWT token payload.

    Contains the claims encoded in the JWT token.
    """

    sub: UUID = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    jti: str | None = Field(None, description="JWT ID (unique token identifier)")
    type: str = Field(default="access", description="Token type (access/refresh)")
    roles: list[str] = Field(
        default_factory=list,
        description="User roles",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="User permissions (resource:action format)",
    )


class TokenResponse(BaseResponse):
    """Schema for token response.

    Contains access and refresh tokens.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )
    refresh_expires_in: int = Field(
        ...,
        description="Refresh token expiration time in seconds",
    )


class TokenRefreshRequest(BaseSchema):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="JWT refresh token")


class TokenVerifyRequest(BaseSchema):
    """Schema for token verification request."""

    token: str = Field(..., description="JWT token to verify")


class TokenVerifyResponse(BaseResponse):
    """Schema for token verification response."""

    valid: bool = Field(..., description="Whether the token is valid")
    payload: TokenPayload | None = Field(None, description="Decoded token payload")
    error: str | None = Field(None, description="Error message if token is invalid")


class PasswordResetRequest(BaseSchema):
    """Schema for password reset request."""

    email: EmailStr = Field(
        ...,
        description="Email address of the user",
        examples=["john@example.com"],
    )


class PasswordResetConfirm(BaseSchema):
    """Schema for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        description="New password",
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < settings.password_min_length:
            raise ValueError(
                f"Password must be at least {settings.password_min_length} characters long"
            )
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class EmailVerificationRequest(BaseSchema):
    """Schema for email verification request."""

    token: str = Field(..., description="Email verification token")


class AuthResponse(BaseResponse):
    """Schema for authentication response with user data."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information")


class LogoutRequest(BaseSchema):
    """Schema for logout request."""

    refresh_token: str | None = Field(
        None,
        description="Refresh token to revoke (optional)",
    )
    all_sessions: bool = Field(
        default=False,
        description="Whether to logout from all sessions",
    )
