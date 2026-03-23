"""Permission endpoints.

This module provides permission management API endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    AuditServiceDep,
    PermissionServiceDep,
    get_client_ip,
)
from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.core.permissions import require_permission
from app.schemas.base import PaginatedResponse, PaginationMeta
from app.schemas.common import PaginationParams
from app.schemas.permission import (
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCreate,
    PermissionListResponse,
    PermissionResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[PermissionResponse])
async def list_permissions(
    params: Annotated[PaginationParams, Depends()],
    resource: str | None = None,
    permission_service: PermissionServiceDep = None,
    current_user: Annotated[dict, Depends(require_permission("permissions", "read"))] = None,
) -> PaginatedResponse[PermissionResponse]:
    """List all permissions with optional filtering.

    Args:
        params: Pagination parameters
        resource: Filter by resource
        permission_service: Permission service
        current_user: Current authenticated user (requires permissions:read permission)

    Returns:
        Paginated list of permissions
    """
    permissions, total = await permission_service.list_permissions(
        skip=params.offset,
        limit=params.limit,
        resource=resource,
    )

    total_pages = (total + params.per_page - 1) // params.per_page if total > 0 else 0

    return PaginatedResponse(
        data=[PermissionResponse.model_validate(p) for p in permissions],
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
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    request: Request,
    permission_data: PermissionCreate,
    permission_service: PermissionServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("permissions", "create"))],
) -> PermissionResponse:
    """Create a new permission.

    Args:
        request: FastAPI request
        permission_data: Permission creation data
        permission_service: Permission service
        audit_service: Audit service
        current_user: Current authenticated user (requires permissions:create permission)

    Returns:
        Created permission
    """
    ip_address = await get_client_ip(request)

    permission = await permission_service.create_permission(permission_data)

    # Log audit
    await audit_service.log_action(
        action="create",
        resource_type="permission",
        resource_id=str(permission.id),
        user_id=uuid.UUID(current_user["id"]),
        new_values={
            "name": permission.name,
            "resource": permission.resource,
            "action": permission.action,
        },
        ip_address=ip_address,
    )

    logger.info(
        "Permission created via API",
        created_by=current_user["id"],
        permission_id=str(permission.id),
        name=permission.name,
    )

    return PermissionResponse.model_validate(permission)


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: uuid.UUID,
    permission_service: PermissionServiceDep,
    current_user: Annotated[dict, Depends(require_permission("permissions", "read"))],
) -> PermissionResponse:
    """Get permission by ID.

    Args:
        permission_id: Permission ID
        permission_service: Permission service
        current_user: Current authenticated user (requires permissions:read permission)

    Returns:
        Permission details
    """
    permission = await permission_service.get_by_id(permission_id)
    return PermissionResponse.model_validate(permission)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    request: Request,
    permission_id: uuid.UUID,
    permission_service: PermissionServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("permissions", "delete"))],
) -> None:
    """Delete permission.

    Args:
        request: FastAPI request
        permission_id: Permission ID to delete
        permission_service: Permission service
        audit_service: Audit service
        current_user: Current authenticated user (requires permissions:delete permission)
    """
    ip_address = await get_client_ip(request)

    # Get permission info before deletion for audit
    permission = await permission_service.get_by_id(permission_id)

    await permission_service.delete_permission(permission_id)

    # Log audit
    await audit_service.log_action(
        action="delete",
        resource_type="permission",
        resource_id=str(permission_id),
        user_id=uuid.UUID(current_user["id"]),
        old_values={
            "name": permission.name,
            "resource": permission.resource,
            "action": permission.action,
        },
        ip_address=ip_address,
    )

    logger.info(
        "Permission deleted via API",
        deleted_by=current_user["id"],
        permission_id=str(permission_id),
        name=permission.name,
    )


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(
    check_data: PermissionCheckRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> PermissionCheckResponse:
    """Check if current user has a specific permission.

    Args:
        check_data: Permission check data
        current_user: Current authenticated user

    Returns:
        Permission check result
    """
    user_permissions = current_user.get("permissions", [])

    # Check if user has the permission
    required = f"{check_data.resource}:{check_data.action}".lower()
    has_permission = False

    # Check exact permission
    if required in [p.lower() for p in user_permissions]:
        has_permission = True

    # Check wildcard permission
    if not has_permission:
        wildcard = f"{check_data.resource.lower()}:*"
        if wildcard in [p.lower() for p in user_permissions]:
            has_permission = True

    # Check superuser
    if not has_permission:
        if "*:*" in user_permissions or "superuser" in current_user.get("roles", []):
            has_permission = True

    return PermissionCheckResponse(
        has_permission=has_permission,
        resource=check_data.resource,
        action=check_data.action,
    )


@router.post("/initialize", response_model=dict)
async def initialize_system_permissions(
    request: Request,
    permission_service: PermissionServiceDep,
    audit_service: AuditServiceDep,
    current_user: Annotated[dict, Depends(require_permission("permissions", "create"))],
) -> dict:
    """Initialize system permissions.

    Creates predefined system permissions if they don't exist.

    Args:
        request: FastAPI request
        permission_service: Permission service
        audit_service: Audit service
        current_user: Current authenticated user (requires permissions:create permission)

    Returns:
        Number of permissions created
    """
    ip_address = await get_client_ip(request)

    created = await permission_service.initialize_system_permissions()

    # Log audit
    await audit_service.log_action(
        action="initialize_system_permissions",
        resource_type="system",
        user_id=uuid.UUID(current_user["id"]),
        new_values={"created_count": len(created)},
        ip_address=ip_address,
    )

    logger.info(
        "System permissions initialized",
        initialized_by=current_user["id"],
        created_count=len(created),
    )

    return {
        "message": "System permissions initialized",
        "created_count": len(created),
    }


@router.get("/by-resource/{resource}", response_model=list[PermissionResponse])
async def get_permissions_by_resource(
    resource: str,
    permission_service: PermissionServiceDep,
    current_user: Annotated[dict, Depends(require_permission("permissions", "read"))],
) -> list[PermissionResponse]:
    """Get all permissions for a resource.

    Args:
        resource: Resource name
        permission_service: Permission service
        current_user: Current authenticated user (requires permissions:read permission)

    Returns:
        List of permissions
    """
    permissions = await permission_service.get_permissions_by_resources([resource])
    return [PermissionResponse.model_validate(p) for p in permissions]
