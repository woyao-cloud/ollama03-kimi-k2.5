"""Audit service module.

This module provides business logic for audit logging operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.models.audit import AuditLog, LoginAttempt, UserSession
from app.domain.models.user import User

logger = get_logger(__name__)


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    # ============================================
    # Audit Log Operations
    # ============================================

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: uuid.UUID | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log an action to the audit log.

        Args:
            action: Action performed (e.g., 'create', 'update', 'delete')
            resource_type: Type of resource affected
            resource_id: ID of the affected resource
            user_id: ID of the user who performed the action
            old_values: Previous values (for updates)
            new_values: New values
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.flush()
        await self.db.refresh(audit_log)

        logger.debug(
            "Audit log created",
            action=action,
            resource_type=resource_type,
            user_id=str(user_id) if user_id else None,
        )

        return audit_log

    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
    ) -> tuple[Sequence[AuditLog], int]:
        """Get audit logs with optional filtering.

        Args:
            skip: Number of logs to skip
            limit: Maximum number of logs to return
            user_id: Filter by user ID
            resource_type: Filter by resource type
            action: Filter by action

        Returns:
            Tuple of (audit logs, total count)
        """
        # Build query
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if action:
            query = query.where(AuditLog.action == action)

        # Order by created_at descending
        query = query.order_by(desc(AuditLog.created_at))

        # Get total count
        count_query = select(AuditLog.id)
        if user_id:
            count_query = count_query.where(AuditLog.user_id == user_id)
        if resource_type:
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        if action:
            count_query = count_query.where(AuditLog.action == action)

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        result = await self.db.execute(
            query.offset(skip).limit(limit)
        )
        logs = result.scalars().all()

        return list(logs), total

    # ============================================
    # Login Attempt Operations
    # ============================================

    async def log_login_attempt(
        self,
        username: str | None = None,
        email: str | None = None,
        was_successful: bool = False,
        failure_reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginAttempt:
        """Log a login attempt.

        Args:
            username: Username attempted
            email: Email attempted
            was_successful: Whether the login was successful
            failure_reason: Reason for failure if unsuccessful
            ip_address: IP address of the attempt
            user_agent: User agent string

        Returns:
            Created login attempt record
        """
        attempt = LoginAttempt(
            username=username,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            was_successful=was_successful,
            failure_reason=failure_reason,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)

        logger.debug(
            "Login attempt logged",
            username=username,
            email=email,
            was_successful=was_successful,
        )

        return attempt

    async def count_failed_attempts(
        self,
        username: str | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        minutes: int = 30,
    ) -> int:
        """Count failed login attempts within a time window.

        Args:
            username: Filter by username
            email: Filter by email
            ip_address: Filter by IP address
            minutes: Time window in minutes

        Returns:
            Number of failed attempts
        """
        from sqlalchemy import and_, func

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(LoginAttempt).where(
            and_(
                LoginAttempt.was_successful == False,
                LoginAttempt.created_at >= cutoff_time,
            )
        )

        if username:
            query = query.where(LoginAttempt.username == username)
        if email:
            query = query.where(LoginAttempt.email == email)
        if ip_address:
            query = query.where(LoginAttempt.ip_address == ip_address)

        result = await self.db.execute(query)
        return len(result.all())

    # ============================================
    # User Session Operations
    # ============================================

    async def create_session(
        self,
        user_id: uuid.UUID,
        token_jti: str | None = None,
        refresh_token_jti: str | None = None,
        expires_at: datetime | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        """Create a new user session.

        Args:
            user_id: User ID
            token_jti: Access token JWT ID
            refresh_token_jti: Refresh token JWT ID
            expires_at: Session expiration time
            ip_address: IP address
            user_agent: User agent string

        Returns:
            Created session
        """
        if expires_at is None:
            # Default 7 days
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            refresh_token_jti=refresh_token_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        logger.debug(
            "User session created",
            session_id=str(session.id),
            user_id=str(user_id),
        )

        return session

    async def get_session_by_token_jti(
        self,
        token_jti: str,
    ) -> UserSession | None:
        """Get session by token JTI.

        Args:
            token_jti: Token JWT ID

        Returns:
            Session or None
        """
        result = await self.db.execute(
            select(UserSession)
            .where(
                UserSession.token_jti == token_jti,
                UserSession.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_session_by_refresh_jti(
        self,
        refresh_token_jti: str,
    ) -> UserSession | None:
        """Get session by refresh token JTI.

        Args:
            refresh_token_jti: Refresh token JWT ID

        Returns:
            Session or None
        """
        result = await self.db.execute(
            select(UserSession)
            .where(
                UserSession.refresh_token_jti == refresh_token_jti,
                UserSession.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        """Revoke a session.

        Args:
            session_id: Session ID to revoke
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            await self.db.flush()

            logger.debug(
                "Session revoked",
                session_id=str(session_id),
            )

    async def revoke_all_user_sessions(
        self,
        user_id: uuid.UUID,
        except_session_id: uuid.UUID | None = None,
    ) -> None:
        """Revoke all sessions for a user.

        Args:
            user_id: User ID
            except_session_id: Optional session ID to keep active
        """
        query = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )

        if except_session_id:
            query = query.where(UserSession.id != except_session_id)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        for session in sessions:
            session.is_active = False

        await self.db.flush()

        logger.info(
            "All user sessions revoked",
            user_id=str(user_id),
            count=len(sessions),
        )

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions deactivated
        """
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.is_active == True,
                UserSession.expires_at < datetime.now(timezone.utc),
            )
        )
        expired_sessions = result.scalars().all()

        for session in expired_sessions:
            session.is_active = False

        await self.db.flush()

        logger.info(
            "Expired sessions cleaned up",
            count=len(expired_sessions),
        )

        return len(expired_sessions)

    async def update_session_activity(
        self,
        session_id: uuid.UUID,
    ) -> None:
        """Update session last activity timestamp.

        Args:
            session_id: Session ID
        """
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.last_activity_at = datetime.now(timezone.utc)
            await self.db.flush()
