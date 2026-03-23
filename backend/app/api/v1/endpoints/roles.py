"""Role endpoints.

This module provides role management API endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    AuditServiceDep,
    PermissionServiceDep,
    RoleServiceDep,
    get_client_ip,
)
from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.core.permissions import require_permission
from app.schemas.base import PaginatedResponse, PaginationMeta
from app.schemas.common import PaginationParams
from app.schemas.permission import PermissionAssignRequest
from app.schemas.role import (
    RoleAssignRequest,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[RoleResponse])
async def list_roles(
    params: Annotated[PaginationParams, Depends()],
    role_service: RoleServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "read"))],
) -> PaginatedResponse[RoleResponse]:
    """List all roles.

    Args:
        params: Pagination parameters
        role_service: Role service
        current_user: Current authenticated user (requires roles:read permission)

    Returns:
        Paginated list of roles
    """
    roles, total = await role_service.list_roles(
        skip=params.offset,
        limit=params.limit,
    )

    total_pages = (total + params.per_page - 1) // params.per_page if total > 0 else 0

    return PaginatedResponse(
        data=[RoleResponse.model_validate(role) for role in roles],
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
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    request: Request,
    role_data: RoleCreate,
    role_service: RoleServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "create"))],
) -> RoleResponse:
    """Create a new role.

    Args:
        request: FastAPI request
        role_data: Role creation data
        role_service: Role service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:create permission)

    Returns:
        Created role
    """
    ip_address = await get_client_ip(request)

    role = await role_service.create_role(role_data)

    # Log audit
    await audit_service.log_action(
        action="create",
        resource_type="role",
        resource_id=str(role.id),
        user_id=uuid.UUID(current_user["id"]),
        new_values={
            "name": role.name,
            "description": role.description,
            "is_default": role.is_default,
        },
        ip_address=ip_address,
    )

    logger.info(
        "Role created via API",
        created_by=current_user["id"],
        role_id=str(role.id),
        name=role.name,
    )

    return RoleResponse.model_validate(role)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: uuid.UUID,
    role_service: RoleServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "read"))],
) -> RoleResponse:
    """Get role by ID.

    Args:
        role_id: Role ID
        role_service: Role service
        current_user: Current authenticated user (requires roles:read permission)

    Returns:
        Role details
    """
    role = await role_service.get_by_id(role_id)
    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    request: Request,
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    role_service: RoleServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "update"))],
) -> RoleResponse:
    """Update role.

    Args:
        request: FastAPI request
        role_id: Role ID to update
        role_data: Role update data
        role_service: Role service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:update permission)

    Returns:
        Updated role
    """
    ip_address = await get_client_ip(request)

    # Get old values for audit
    old_role = await role_service.get_by_id(role_id)
    old_values = {
        "name": old_role.name,
        "description": old_role.description,
        "is_default": old_role.is_default,
    }

    role = await role_service.update_role(role_id, role_data)

    # Log audit
    new_values = {
        "name": role.name,
        "description": role.description,
        "is_default": role.is_default,
    }

    await audit_service.log_action(
        action="update",
        resource_type="role",
        resource_id=str(role.id),
        user_id=uuid.UUID(current_user["id"]),
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )

    logger.info(
        "Role updated via API",
        updated_by=current_user["id"],
        role_id=str(role_id),
        name=role.name,
    )

    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    request: Request,
    role_id: uuid.UUID,
    role_service: RoleServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "delete"))],
) -> None:
    """Delete role.

    Args:
        request: FastAPI request
        role_id: Role ID to delete
        role_service: Role service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:delete permission)
    """
    ip_address = await get_client_ip(request)

    # Get role info before deletion for audit
    role = await role_service.get_by_id(role_id)

    await role_service.delete_role(role_id)

    # Log audit
    await audit_service.log_action(
        action="delete",
        resource_type="role",
        resource_id=str(role_id),
        user_id=uuid.UUID(current_user["id"]),
        old_values={
            "name": role.name,
            "description": role.description,
        },
        ip_address=ip_address,
    )

    logger.info(
        "Role deleted via API",
        deleted_by=current_user["id"],
        role_id=str(role_id),
        name=role.name,
    )


@router.post("/{role_id}/permissions", response_model=RoleResponse)
async def assign_permissions_to_role(
    request: Request,
    role_id: uuid.UUID,
    permission_data: PermissionAssignRequest,
    role_service: RoleServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "update"))],
) -> RoleResponse:
    """Assign permissions to a role.

    Args:
        request: FastAPI request
        role_id: Role ID
        permission_data: Permission assignment data
        role_service: Role service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:update permission)

    Returns:
        Updated role
    """
    ip_address = await get_client_ip(request)

    role = await role_service.assign_permissions(role_id, permission_data.permission_ids)

    # Log audit
    await audit_service.log_action(
        action="assign_permissions",
        resource_type="role",
        resource_id=str(role_id),
        user_id=uuid.UUID(current_user["id"]),
        new_values={"permission_ids": [str(pid) for pid in permission_data.permission_ids]},
        ip_address=ip_address,
    )

    logger.info(
        "Permissions assigned to role",
        assigned_by=current_user["id"],
        role_id=str(role_id),
        permission_ids=[str(pid) for pid in permission_data.permission_ids],
    )

    return RoleResponse.model_validate(role)


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleResponse)
async def remove_permission_from_role(
    request: Request,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    role_service: RoleServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("roles", "update"))],
) -> RoleResponse:
    """Remove a permission from a role.

    Args:
        request: FastAPI request
        role_id: Role ID
        permission_id: Permission ID to remove
        role_service: Role service
        audit_service: Audit service
        current_user: Current authenticated user (requires roles:update permission)

    Returns:
        Updated role
    """
    ip_address = await get_client_ip(request)

    role = await role_service.remove_permission(role_id, permission_id)

    # Log audit
    await audit_service.log_action(
        action="remove_permission",
        resource_type="role",
        resource_id=str(role_id),
        user_id=uuid.UUID(current_user["id"]),
        old_values={"permission_id": str(permission_id)},
        ip_address=ip_address,
    )

    logger.info(
        "Permission removed from role",
        removed_by=current_user["id"],
        role_id=str(role_id),
        permission_id=str(permission_id),
    )

    return RoleResponse.model_validate(role)
