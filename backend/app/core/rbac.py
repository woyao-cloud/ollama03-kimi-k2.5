"""Role-based access control utilities.

This module provides dependencies and utilities for role-based
access control (RBAC).
"""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)


def has_role(user_roles: list[str], required_role: str) -> bool:
    """Check if user has a specific role.

    Args:
        user_roles: List of user's roles
        required_role: Required role name

    Returns:
        True if user has the role
    """
    required = required_role.lower()

    # Check for exact role match
    if required in [role.lower() for role in user_roles]:
        return True

    # Superuser has all roles implicitly
    if "superuser" in [role.lower() for role in user_roles]:
        return True

    return False


def has_any_role(user_roles: list[str], required_roles: list[str]) -> bool:
    """Check if user has any of the required roles.

    Args:
        user_roles: List of user's roles
        required_roles: List of required role names

    Returns:
        True if user has any role
    """
    return any(has_role(user_roles, role) for role in required_roles)


def has_all_roles(user_roles: list[str], required_roles: list[str]) -> bool:
    """Check if user has all of the required roles.

    Args:
        user_roles: List of user's roles
        required_roles: List of required role names

    Returns:
        True if user has all roles
    """
    return all(has_role(user_roles, role) for role in required_roles)


def require_role(role: str) -> Callable:
    """Dependency factory that requires a specific role.

    Args:
        role: Required role name

    Returns:
        Dependency function

    Example:
        ```python
        @router.get("/admin-only")
        async def admin_endpoint(
            user: dict = Depends(require_role("admin"))
        ):
            pass
        ```
    """
    async def check_role(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_roles = current_user.get("roles", [])

        if not has_role(user_roles, role):
            logger.warning(
                "Role check failed",
                user_id=current_user.get("id"),
                required_role=role,
                user_roles=user_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )

        return current_user

    return check_role


def require_any_role(*roles: str) -> Callable:
    """Dependency factory that requires any of the specified roles.

    Args:
        *roles: Required role names

    Returns:
        Dependency function

    Example:
        ```python
        @router.get("/moderator-only")
        async def moderator_endpoint(
            user: dict = Depends(require_any_role("admin", "moderator"))
        ):
            pass
        ```
    """
    async def check_any_role(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_roles = current_user.get("roles", [])

        if not has_any_role(user_roles, list(roles)):
            logger.warning(
                "Role check failed - requires any of",
                user_id=current_user.get("id"),
                required_roles=roles,
                user_roles=user_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {list(roles)} required",
            )

        return current_user

    return check_any_role


def require_all_roles(*roles: str) -> Callable:
    """Dependency factory that requires all of the specified roles.

    Args:
        *roles: Required role names

    Returns:
        Dependency function

    Example:
        ```python
        @router.get("/super-moderator")
        async def super_moderator_endpoint(
            user: dict = Depends(require_all_roles("admin", "moderator"))
        ):
            pass
        ```
    """
    async def check_all_roles(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_roles = current_user.get("roles", [])

        if not has_all_roles(user_roles, list(roles)):
            logger.warning(
                "Role check failed - requires all of",
                user_id=current_user.get("id"),
                required_roles=roles,
                user_roles=user_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All roles {list(roles)} required",
            )

        return current_user

    return check_all_roles


class RoleChecker:
    """Class-based role checker for more complex scenarios."""

    def __init__(self, *required_roles: str, require_all: bool = False):
        """Initialize with required roles.

        Args:
            *required_roles: Required role names
            require_all: If True, user must have all roles; if False, any role
        """
        self.required_roles = required_roles
        self.require_all = require_all

    async def __call__(
        self,
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        """Check if user has required roles.

        Args:
            current_user: Current authenticated user

        Returns:
            User data if authorized

        Raises:
            HTTPException: If user lacks required roles
        """
        user_roles = current_user.get("roles", [])

        if self.require_all:
            authorized = has_all_roles(user_roles, list(self.required_roles))
            error_msg = f"All roles {list(self.required_roles)} required"
        else:
            authorized = has_any_role(user_roles, list(self.required_roles))
            error_msg = f"One of roles {list(self.required_roles)} required"

        if not authorized:
            logger.warning(
                "Role check failed",
                user_id=current_user.get("id"),
                required_roles=self.required_roles,
                require_all=self.require_all,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )

        return current_user


# Predefined role checkers
require_admin = require_role("admin")
require_superuser = require_role("superuser")
require_user = require_role("user")


# Convenience function
def is_admin(user: dict) -> bool:
    """Check if user is admin.

    Args:
        user: User data dictionary

    Returns:
        True if user is admin or superuser
    """
    roles = user.get("roles", [])
    return has_any_role(roles, ["admin", "superuser"])


def is_superuser(user: dict) -> bool:
    """Check if user is superuser.

    Args:
        user: User data dictionary

    Returns:
        True if user is superuser
    """
    roles = user.get("roles", [])
    return has_role(roles, "superuser")
