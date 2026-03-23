"""Permission checking utilities.

This module provides dependencies and decorators for permission-based
access control (RBAC).
"""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.core.exceptions import AuthorizationException
from app.core.logging import get_logger

logger = get_logger(__name__)


def has_permission(
    user_permissions: list[str],
    required_resource: str,
    required_action: str,
) -> bool:
    """Check if user has a specific permission.

    Args:
        user_permissions: List of user's permissions (format: "resource:action")
        required_resource: Required resource
        required_action: Required action

    Returns:
        True if user has permission
    """
    required = f"{required_resource.lower()}:{required_action.lower()}"

    # Check for exact permission
    if required in user_permissions:
        return True

    # Check for wildcard permission (e.g., "users:*")
    wildcard = f"{required_resource.lower()}:*"
    if wildcard in user_permissions:
        return True

    # Check for superuser permission
    if "*:*" in user_permissions or "superuser" in user_permissions:
        return True

    return False


def has_any_permission(
    user_permissions: list[str],
    required_permissions: list[tuple[str, str]],
) -> bool:
    """Check if user has any of the required permissions.

    Args:
        user_permissions: List of user's permissions
        required_permissions: List of (resource, action) tuples

    Returns:
        True if user has any permission
    """
    return any(
        has_permission(user_permissions, resource, action)
        for resource, action in required_permissions
    )


def has_all_permissions(
    user_permissions: list[str],
    required_permissions: list[tuple[str, str]],
) -> bool:
    """Check if user has all of the required permissions.

    Args:
        user_permissions: List of user's permissions
        required_permissions: List of (resource, action) tuples

    Returns:
        True if user has all permissions
    """
    return all(
        has_permission(user_permissions, resource, action)
        for resource, action in required_permissions
    )


def require_permission(resource: str, action: str) -> Callable:
    """Dependency factory that requires a specific permission.

    Args:
        resource: Required resource
        action: Required action

    Returns:
        Dependency function

    Example:
        ```python
        @router.post("/")
        async def create_user(
            user: dict = Depends(require_permission("users", "create"))
        ):
            pass
        ```
    """
    async def check_permission(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_permissions = current_user.get("permissions", [])

        if not has_permission(user_permissions, resource, action):
            logger.warning(
                "Permission denied",
                user_id=current_user.get("id"),
                required=f"{resource}:{action}",
                permissions=user_permissions,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}:{action} required",
            )

        return current_user

    return check_permission


def require_any_permission(
    *permissions: tuple[str, str],
) -> Callable:
    """Dependency factory that requires any of the specified permissions.

    Args:
        *permissions: Tuple of (resource, action) pairs

    Returns:
        Dependency function

    Example:
        ```python
        @router.get("/")
        async def list_users(
            user: dict = Depends(require_any_permission(
                ("users", "read"),
                ("admin", "read")
            ))
        ):
            pass
        ```
    """
    async def check_any_permission(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_permissions = current_user.get("permissions", [])

        if not has_any_permission(user_permissions, list(permissions)):
            logger.warning(
                "Permission denied - requires any of",
                user_id=current_user.get("id"),
                required=[f"{r}:{a}" for r, a in permissions],
                permissions=user_permissions,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return check_any_permission


def require_all_permissions(
    *permissions: tuple[str, str],
) -> Callable:
    """Dependency factory that requires all of the specified permissions.

    Args:
        *permissions: Tuple of (resource, action) pairs

    Returns:
        Dependency function

    Example:
        ```python
        @router.post("/admin-action")
        async def admin_action(
            user: dict = Depends(require_all_permissions(
                ("users", "read"),
                ("users", "update")
            ))
        ):
            pass
        ```
    """
    async def check_all_permissions(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_permissions = current_user.get("permissions", [])

        if not has_all_permissions(user_permissions, list(permissions)):
            logger.warning(
                "Permission denied - requires all of",
                user_id=current_user.get("id"),
                required=[f"{r}:{a}" for r, a in permissions],
                permissions=user_permissions,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return check_all_permissions


class PermissionChecker:
    """Class-based permission checker for more complex scenarios."""

    def __init__(self, *required_permissions: tuple[str, str]):
        """Initialize with required permissions.

        Args:
            *required_permissions: Tuple of (resource, action) pairs
        """
        self.required_permissions = required_permissions

    async def __call__(
        self,
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        """Check if user has required permissions.

        Args:
            current_user: Current authenticated user

        Returns:
            User data if authorized

        Raises:
            HTTPException: If user lacks required permissions
        """
        user_permissions = current_user.get("permissions", [])

        # Check each required permission
        for resource, action in self.required_permissions:
            if has_permission(user_permissions, resource, action):
                return current_user

        # None of the required permissions matched
        logger.warning(
            "Permission denied",
            user_id=current_user.get("id"),
            required=[f"{r}:{a}" for r, a in self.required_permissions],
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


# Convenience function for creating permission dependencies
def can(resource: str, action: str) -> Callable:
    """Shorthand for require_permission.

    Args:
        resource: Resource name
        action: Action name

    Returns:
        Dependency function

    Example:
        ```python
        @router.post("/users")
        async def create_user(
            user: dict = Depends(can("users", "create"))
        ):
            pass
        ```
    """
    return require_permission(resource, action)
