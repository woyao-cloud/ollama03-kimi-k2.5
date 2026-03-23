"""API dependencies module.

This module provides FastAPI dependencies for database sessions
and service injection.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.audit_service import AuditService
from app.application.services.auth_service import AuthService
from app.application.services.permission_service import PermissionService
from app.application.services.role_service import RoleService
from app.application.services.user_service import UserService
from app.core.logging import get_logger
from app.infrastructure.database.session import AsyncSessionLocal

logger = get_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as dependency.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for database dependency
DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_user_service(db: DbDep) -> UserService:
    """Get user service with database session.

    Args:
        db: Database session

    Returns:
        UserService instance
    """
    return UserService(db)


async def get_auth_service(db: DbDep) -> AuthService:
    """Get authentication service with database session.

    Args:
        db: Database session

    Returns:
        AuthService instance
    """
    return AuthService(db)


async def get_role_service(db: DbDep) -> RoleService:
    """Get role service with database session.

    Args:
        db: Database session

    Returns:
        RoleService instance
    """
    return RoleService(db)


async def get_permission_service(db: DbDep) -> PermissionService:
    """Get permission service with database session.

    Args:
        db: Database session

    Returns:
        PermissionService instance
    """
    return PermissionService(db)


async def get_audit_service(db: DbDep) -> AuditService:
    """Get audit service with database session.

    Args:
        db: Database session

    Returns:
        AuditService instance
    """
    return AuditService(db)


# Service type aliases
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
PermissionServiceDep = Annotated[PermissionService, Depends(get_permission_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]


async def get_client_ip(request: Request) -> str:
    """Extract client IP from request.

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_user_agent(request: Request) -> str:
    """Extract user agent from request.

    Args:
        request: FastAPI request

    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")
