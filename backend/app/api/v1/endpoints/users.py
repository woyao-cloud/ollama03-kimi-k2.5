"""User endpoints.

This module provides user management API endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    AuditServiceDep,
    RoleServiceDep,
    UserServiceDep,
    get_client_ip,
)
from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.core.permissions import can, require_permission
from app.core.rbac import require_admin
from app.schemas.base import PaginatedResponse, PaginationMeta
from app.schemas.common import PaginationParams, UserFilterParams
from app.schemas.role import RoleAssignRequest
from app.schemas.user import (
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    params: Annotated[PaginationParams, Depends()],
    filters: Annotated[UserFilterParams, Depends()],
    user_service: UserServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "read"))],
) -> PaginatedResponse[UserResponse]:
    """List all users with optional filtering.

    Args:
        params: Pagination parameters
        filters: Filter parameters
        user_service: User service
        current_user: Current authenticated user (requires users:read permission)

    Returns:
        Paginated list of users
    """
    users, total = await user_service.list_users(
        skip=params.offset,
        limit=params.limit,
        is_active=filters.is_active,
        is_verified=filters.is_verified,
    )

    # Calculate pagination metadata
    total_pages = (total + params.per_page - 1) // params.per_page if total > 0 else 0

    return PaginatedResponse(
        data=[UserResponse.model_validate(user) for user in users],
        meta=PaginationMeta(
            page=params.page,
            per_page=params.per_page,
            total=total,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        ),
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: Request,
    user_data: UserCreate,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "create"))],
) -> UserResponse:
    """Create a new user.

    Args:
        request: FastAPI request
        user_data: User creation data
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires users:create permission)

    Returns:
        Created user
    """
    ip_address = await get_client_ip(request)

    # Create user
    user = await user_service.create_user(user_data)

    # Log audit
    await audit_service.log_action(
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        user_id=uuid.UUID(current_user["id"]),
        new_values={
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        ip_address=ip_address,
    )

    logger.info(
        "User created via API",
        created_by=current_user["id"],
        new_user_id=str(user.id),
        username=user.username,
    )

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "read"))],
) -> UserResponse:
    """Get user by ID.

    Args:
        user_id: User ID
        user_service: User service
        current_user: Current authenticated user (requires users:read permission)

    Returns:
        User details
    """
    # Users can always read their own data
    if str(user_id) != current_user["id"]:
        # Otherwise require read permission
        pass  # Permission already checked by dependency

    user = await user_service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    user_data: UserUpdate,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "update"))],
) -> UserResponse:
    """Update user.

    Args:
        request: FastAPI request
        user_id: User ID to update
        user_data: User update data
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires users:update permission)

    Returns:
        Updated user
    """
    ip_address = await get_client_ip(request)

    # Get old values for audit
    old_user = await user_service.get_by_id(user_id)
    old_values = {
        "username": old_user.username,
        "email": old_user.email,
        "first_name": old_user.first_name,
        "last_name": old_user.last_name,
        "is_active": old_user.is_active,
        "is_verified": old_user.is_verified,
    }

    # Update user
    user = await user_service.update_user(user_id, user_data)

    # Log audit
    new_values = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
    }

    await audit_service.log_action(
        action="update",
        resource_type="user",
        resource_id=str(user.id),
        user_id=uuid.UUID(current_user["id"]),
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )

    logger.info(
        "User updated via API",
        updated_by=current_user["id"],
        user_id=str(user_id),
    )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "delete"))],
) -> None:
    """Delete user.

    Args:
        request: FastAPI request
        user_id: User ID to delete
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires users:delete permission)

    Raises:
        HTTPException: If trying to delete self
    """
    # Prevent self-deletion
    if str(user_id) == current_user["id"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account through this endpoint",
        )

    ip_address = await get_client_ip(request)

    # Get user info before deletion for audit
    user = await user_service.get_by_id(user_id)

    # Delete user
    await user_service.delete_user(user_id)

    # Log audit
    await audit_service.log_action(
        action="delete",
        resource_type="user",
        resource_id=str(user_id),
        user_id=uuid.UUID(current_user["id"]),
        old_values={
            "username": user.username,
            "email": user.email,
        },
        ip_address=ip_address,
    )

    logger.info(
        "User deleted via API",
        deleted_by=current_user["id"],
        user_id=str(user_id),
        username=user.username,
    )


@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_roles_to_user(
    request: Request,
    user_id: uuid.UUID,
    role_data: RoleAssignRequest,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "update"))],
) -> UserResponse:
    """Assign roles to a user.

    Args:
        request: FastAPI request
        user_id: User ID
        role_data: Role assignment data
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:update permission)

    Returns:
        Updated user
    """
    ip_address = await get_client_ip(request)

    user = await user_service.assign_roles(user_id, role_data.role_ids)

    # Log audit
    await audit_service.log_action(
        action="assign_roles",
        resource_type="user",
        resource_id=str(user_id),
        user_id=uuid.UUID(current_user["id"]),
        new_values={"role_ids": [str(rid) for rid in role_data.role_ids]},
        ip_address=ip_address,
    )

    logger.info(
        "Roles assigned to user",
        assigned_by=current_user["id"],
        user_id=str(user_id),
        role_ids=[str(rid) for rid in role_data.role_ids],
    )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse)
async def remove_role_from_user(
    request: Request,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "update"))],
) -> UserResponse:
    """Remove a role from a user.

    Args:
        request: FastAPI request
        user_id: User ID
        role_id: Role ID to remove
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:update permission)

    Returns:
        Updated user
    """
    ip_address = await get_client_ip(request)

    user = await user_service.remove_role(user_id, role_id)

    # Log audit
    await audit_service.log_action(
        action="remove_role",
        resource_type="user",
        resource_id=str(user_id),
        user_id=uuid.UUID(current_user["id"]),
        old_values={"role_id": str(role_id)},
        ip_address=ip_address,
    )

    logger.info(
        "Role removed from user",
        removed_by=current_user["id"],
        user_id=str(user_id),
        role_id=str(role_id),
    )

    return UserResponse.model_validate(user)


@router.put("/{user_id}/password", response_model=dict)
async def admin_update_password(
    request: Request,
    user_id: uuid.UUID,
    new_password: str,
    user_service: UserServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("users", "update"))],
) -> dict:
    """Admin endpoint to update user password without current password.

    Args:
        request: FastAPI request
        user_id: User ID
        new_password: New password
        user_service: User service
        audit_service: Audit service
        current_user: Current authenticated user (requires users:update permission)

    Returns:
        Success message
    """
    ip_address = await get_client_ip(request)

    await user_service.update_password(user_id, new_password)

    # Log audit
    await audit_service.log_action(
        action="password_reset",
        resource_type="user",
        resource_id=str(user_id),
        user_id=uuid.UUID(current_user["id"]),
        ip_address=ip_address,
    )

    logger.info(
        "User password updated by admin",
        updated_by=current_user["id"],
        user_id=str(user_id),
    )

    return {"message": "Password updated successfully"}
