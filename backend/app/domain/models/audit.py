"""Audit domain models.

This module defines audit models for tracking user actions, sessions, and login attempts.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, BaseModel


class AuditLog(BaseModel):
    """Audit log model for tracking all operations.

    Attributes:
        id: Unique identifier (UUID)
        user_id: ID of the user who performed the action
        action: Action performed (e.g., 'create', 'update', 'delete', 'login')
        resource_type: Type of resource affected (e.g., 'user', 'role')
        resource_id: ID of the affected resource
        old_values: Previous values (for updates)
        new_values: New values
        ip_address: IP address of the request
        user_agent: User agent string
        created_at: When the action occurred
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    old_values: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    new_values: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        """String representation of the audit log."""
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"


class UserSession(Base):
    """User session model for managing active sessions.

    Attributes:
        id: Unique identifier (UUID)
        user_id: ID of the user
        token_jti: JWT token unique identifier (jti claim)
        refresh_token_jti: Refresh token unique identifier
        ip_address: IP address of the session
        user_agent: User agent string
        is_active: Whether the session is active
        expires_at: Session expiration time
        created_at: Session creation time
        last_activity_at: Last activity timestamp
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_jti: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )
    refresh_token_jti: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        """String representation of the user session."""
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class LoginAttempt(Base):
    """Login attempt model for security auditing.

    Attributes:
        id: Unique identifier (UUID)
        username: Username attempted
        email: Email attempted
        ip_address: IP address of the attempt
        user_agent: User agent string
        was_successful: Whether the login was successful
        failure_reason: Reason for failure if unsuccessful
        created_at: When the attempt occurred
    """

    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    was_successful: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of the login attempt."""
        return f"<LoginAttempt(id={self.id}, username={self.username}, was_successful={self.was_successful})>"
