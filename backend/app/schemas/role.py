"""Role Pydantic schemas.

This module defines schemas for role-related operations.
"""

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseCreateSchema, BaseInDBSchema, BaseResponse, BaseUpdateSchema
from app.schemas.permission import PermissionResponse


class RoleBase(BaseCreateSchema):
    """Base role schema with common fields."""

    name: str = Field(
        ...,
        description="Unique role name",
        min_length=1,
        max_length=50,
        examples=["admin", "user", "moderator"],
    )
    description: str | None = Field(
        None,
        description="Role description",
        examples=["Administrator with full access"],
    )
    is_default: bool = Field(
        default=False,
        description="Whether this role is assigned to new users by default",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name.

        Role names should be lowercase with no spaces.
        """
        v = v.strip().lower()
        if " " in v:
            raise ValueError("Role name cannot contain spaces")
        if not v.isalnum() and "_" not in v:
            raise ValueError("Role name can only contain letters, numbers, and underscores")
        return v


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    permission_ids: list[UUID] = Field(
        default_factory=list,
        description="List of permission IDs to assign to this role",
    )


class RoleUpdate(BaseUpdateSchema):
    """Schema for updating an existing role.

    All fields are optional to allow partial updates.
    """

    name: str | None = Field(
        None,
        description="Unique role name",
        min_length=1,
        max_length=50,
        examples=["admin", "user"],
    )
    description: str | None = Field(
        None,
        description="Role description",
    )
    is_default: bool | None = Field(
        None,
        description="Whether this role is assigned to new users by default",
    )
    permission_ids: list[UUID] | None = Field(
        None,
        description="List of permission IDs to assign to this role",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate role name."""
        if v is None:
            return v
        v = v.strip().lower()
        if " " in v:
            raise ValueError("Role name cannot contain spaces")
        if not v.isalnum() and "_" not in v:
            raise ValueError("Role name can only contain letters, numbers, and underscores")
        return v


class RoleResponse(RoleBase, BaseInDBSchema):
    """Schema for role response.

    Includes permissions associated with the role.
    """

    permissions: list[PermissionResponse] = Field(
        default_factory=list,
        description="Permissions granted by this role",
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class RoleInDB(RoleBase, BaseInDBSchema):
    """Schema for role as stored in database."""

    pass


class RoleAssignRequest(BaseCreateSchema):
    """Schema for assigning roles to a user."""

    role_ids: list[UUID] = Field(
        ...,
        description="List of role IDs to assign",
        min_length=1,
    )


class RoleListResponse(BaseResponse):
    """Schema for role list response."""

    roles: list[RoleResponse] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles")
