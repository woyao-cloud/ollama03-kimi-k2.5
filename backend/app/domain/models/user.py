"""User domain model.

This module defines the User model for authentication and user management.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from app.domain.models.role import Role


class User(BaseModel):
    """User model for authentication and user management.

    Attributes:
        id: Unique identifier (UUID)
        username: Unique username
        email: Unique email address
        password_hash: Hashed password
        first_name: First name
        last_name: Last name
        is_active: Whether the account is active
        is_verified: Whether the email is verified
        last_login_at: Last login timestamp
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        roles: Associated roles
    """

    __tablename__ = "users"

    # Authentication fields
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile fields
    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username

    @property
    def is_superuser(self) -> bool:
        """Check if user has superuser role."""
        return any(role.name == "superuser" for role in self.roles)

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role.

        Args:
            role_name: Name of the role to check

        Returns:
            True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has a specific permission.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            True if user has the permission, False otherwise
        """
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False
