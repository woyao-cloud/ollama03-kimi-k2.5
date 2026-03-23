"""Permission Pydantic schemas.

This module defines schemas for permission-related operations.
"""

import uuid

from pydantic import Field, field_validator

from app.schemas.base import BaseCreateSchema, BaseInDBSchema, BaseResponse


class PermissionBase(BaseCreateSchema):
    """Base permission schema with common fields."""

    name: str = Field(
        ...,
        description="Unique permission name",
        min_length=1,
        max_length=100,
        examples=["users:read", "users:write", "roles:read"],
    )
    resource: str = Field(
        ...,
        description="Resource being controlled (e.g., 'users', 'roles')",
        min_length=1,
        max_length=50,
        examples=["users", "roles", "permissions"],
    )
    action: str = Field(
        ...,
        description="Action being performed (e.g., 'create', 'read', 'update', 'delete')",
        min_length=1,
        max_length=50,
        examples=["create", "read", "update", "delete"],
    )

    @field_validator("resource", "action")
    @classmethod
    def validate_lowercase(cls, v: str) -> str:
        """Validate that resource and action are lowercase."""
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate permission name format.

        Permission names should be in format 'resource:action'.
        """
        v = v.lower()
        if ":" not in v:
            raise ValueError("Permission name must be in format 'resource:action'")
        return v


class PermissionCreate(PermissionBase):
    """Schema for creating a new permission."""

    pass


class PermissionUpdate(BaseCreateSchema):
    """Schema for updating an existing permission.

    Note: Permissions are typically immutable. Updates should be rare.
    """

    name: str | None = Field(
        None,
        description="Unique permission name",
        max_length=100,
    )
    resource: str | None = Field(
        None,
        description="Resource being controlled",
        max_length=50,
    )
    action: str | None = Field(
        None,
        description="Action being performed",
        max_length=50,
    )


class PermissionResponse(PermissionBase, BaseInDBSchema):
    """Schema for permission response."""

    class Config:
        """Pydantic config."""

        from_attributes = True


class PermissionInDB(PermissionBase, BaseInDBSchema):
    """Schema for permission as stored in database."""

    pass


class PermissionListResponse(BaseResponse):
    """Schema for permission list response."""

    permissions: list[PermissionResponse] = Field(..., description="List of permissions")
    total: int = Field(..., description="Total number of permissions")


class PermissionCheckRequest(BaseCreateSchema):
    """Schema for checking if user has permission."""

    resource: str = Field(..., description="Resource to check", examples=["users"])
    action: str = Field(..., description="Action to check", examples=["create"])


class PermissionCheckResponse(BaseResponse):
    """Schema for permission check response."""

    has_permission: bool = Field(..., description="Whether the user has the permission")
    resource: str = Field(..., description="Resource checked")
    action: str = Field(..., description="Action checked")


class PermissionAssignRequest(BaseCreateSchema):
    """Schema for assigning permissions to a role."""

    permission_ids: list[uuid.UUID] = Field(
        ...,
        description="List of permission IDs to assign",
        min_length=1,
    )
