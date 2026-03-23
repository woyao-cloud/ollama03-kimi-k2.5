"""Role domain model.

This module defines the Role model for role-based access control (RBAC).
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from app.domain.models.permission import Permission
    from app.domain.models.user import User


class Role(BaseModel):
    """Role model for RBAC.

    Attributes:
        id: Unique identifier (UUID)
        name: Unique role name
        description: Role description
        is_default: Whether this role is assigned to new users by default
        created_at: Role creation timestamp
        updated_at: Last update timestamp
        users: Users with this role
        permissions: Permissions granted by this role
    """

    __tablename__ = "roles"

    # Role fields
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role(id={self.id}, name={self.name})>"

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if role has a specific permission.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            True if role has the permission, False otherwise
        """
        return any(
            permission.resource == resource and permission.action == action
            for permission in self.permissions
        )
