"""Permission domain model.

This module defines the Permission model for role-based access control (RBAC).
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from app.domain.models.role import Role


class Permission(BaseModel):
    """Permission model for RBAC.

    Attributes:
        id: Unique identifier (UUID)
        name: Unique permission name
        resource: Resource being controlled (e.g., 'users', 'roles')
        action: Action being performed (e.g., 'create', 'read', 'update', 'delete')
        created_at: Permission creation timestamp
        updated_at: Last update timestamp
        roles: Roles that have this permission
    """

    __tablename__ = "permissions"

    # Permission fields
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    resource: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"

    @property
    def full_permission(self) -> str:
        """Get full permission string in format 'resource:action'."""
        return f"{self.resource}:{self.action}"
