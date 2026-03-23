"""User Pydantic schemas.

This module defines schemas for user-related operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.config import settings
from app.schemas.base import BaseCreateSchema, BaseInDBSchema, BaseResponse, BaseUpdateSchema
from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    """Base user schema with common fields."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(
        ...,
        description="Unique username",
        min_length=3,
        max_length=50,
        examples=["johndoe"],
    )
    email: EmailStr = Field(
        ...,
        description="Email address",
        examples=["john@example.com"],
    )
    first_name: str | None = Field(
        None,
        description="First name",
        max_length=100,
        examples=["John"],
    )
    last_name: str | None = Field(
        None,
        description="Last name",
        max_length=100,
        examples=["Doe"],
    )


class UserCreate(UserBase, BaseCreateSchema):
    """Schema for creating a new user.

    Includes password field for initial user creation.
    """

    password: str = Field(
        ...,
        description="User password",
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
        examples=["SecurePassword123!"],
    )

    @field_validator("password")
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


class UserUpdate(BaseUpdateSchema):
    """Schema for updating an existing user.

    All fields are optional to allow partial updates.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str | None = Field(
        None,
        description="Unique username",
        min_length=3,
        max_length=50,
        examples=["johndoe"],
    )
    email: EmailStr | None = Field(
        None,
        description="Email address",
        examples=["john@example.com"],
    )
    first_name: str | None = Field(
        None,
        description="First name",
        max_length=100,
        examples=["John"],
    )
    last_name: str | None = Field(
        None,
        description="Last name",
        max_length=100,
        examples=["Doe"],
    )
    is_active: bool | None = Field(
        None,
        description="Whether the user account is active",
    )
    is_verified: bool | None = Field(
        None,
        description="Whether the user email is verified",
    )


class UserPasswordUpdate(BaseSchema):
    """Schema for updating user password."""

    current_password: str = Field(
        ...,
        description="Current password",
    )
    new_password: str = Field(
        ...,
        description="New password",
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
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


class UserResponse(UserBase, BaseInDBSchema):
    """Schema for user response.

    Excludes sensitive fields like password_hash.
    """

    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user email is verified")
    last_login_at: datetime | None = Field(
        None, description="Last login timestamp"
    )
    roles: list[RoleResponse] = Field(
        default_factory=list,
        description="User roles",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username


class UserInDB(UserBase, BaseInDBSchema):
    """Schema for user as stored in database.

    Includes sensitive fields - do not expose in API responses.
    """

    password_hash: str = Field(..., description="Hashed password")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user email is verified")
    last_login_at: datetime | None = Field(
        None, description="Last login timestamp"
    )


class UserListResponse(BaseResponse):
    """Schema for user list response."""

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
