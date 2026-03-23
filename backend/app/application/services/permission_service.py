"""Permission service module.

This module provides business logic for permission management operations.
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.domain.models.permission import Permission
from app.schemas.permission import PermissionCreate

logger = get_logger(__name__)


class PermissionService:
    """Service for permission management operations."""

    # Predefined system permissions
    SYSTEM_PERMISSIONS = [
        # User permissions
        ("users:create", "users", "create"),
        ("users:read", "users", "read"),
        ("users:update", "users", "update"),
        ("users:delete", "users", "delete"),
        # Role permissions
        ("roles:create", "roles", "create"),
        ("roles:read", "roles", "read"),
        ("roles:update", "roles", "update"),
        ("roles:delete", "roles", "delete"),
        # Permission permissions
        ("permissions:create", "permissions", "create"),
        ("permissions:read", "permissions", "read"),
        ("permissions:update", "permissions", "update"),
        ("permissions:delete", "permissions", "delete"),
    ]

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_id(self, permission_id: uuid.UUID) -> Permission:
        """Get permission by ID.

        Args:
            permission_id: Permission UUID

        Returns:
            Permission model instance

        Raises:
            NotFoundException: If permission not found
        """
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            logger.warning("Permission not found", permission_id=str(permission_id))
            raise NotFoundException("Permission", str(permission_id))

        return permission

    async def get_by_name(self, name: str) -> Permission | None:
        """Get permission by name.

        Args:
            name: Permission name (format: "resource:action")

        Returns:
            Permission model instance or None
        """
        result = await self.db.execute(
            select(Permission).where(Permission.name == name.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_resource_action(
        self,
        resource: str,
        action: str,
    ) -> Permission | None:
        """Get permission by resource and action.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            Permission model instance or None
        """
        result = await self.db.execute(
            select(Permission)
            .where(
                Permission.resource == resource.lower(),
                Permission.action == action.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def list_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        resource: str | None = None,
    ) -> tuple[Sequence[Permission], int]:
        """List all permissions.

        Args:
            skip: Number of permissions to skip
            limit: Maximum number of permissions to return
            resource: Filter by resource

        Returns:
            Tuple of (permissions list, total count)
        """
        # Build query
        query = select(Permission)

        if resource:
            query = query.where(Permission.resource == resource.lower())

        # Get total count
        count_query = select(Permission.id)
        if resource:
            count_query = count_query.where(Permission.resource == resource.lower())

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        result = await self.db.execute(
            query.offset(skip).limit(limit)
        )
        permissions = result.scalars().all()

        return list(permissions), total

    async def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission.

        Args:
            permission_data: Permission creation data

        Returns:
            Created permission model

        Raises:
            ConflictException: If permission already exists
        """
        # Generate permission name
        name = f"{permission_data.resource}:{permission_data.action}"

        # Check for existing permission
        existing = await self.get_by_name(name)
        if existing:
            raise ConflictException(
                f"Permission '{name}' already exists",
                field="name",
            )

        # Create permission
        permission = Permission(
            name=name.lower(),
            resource=permission_data.resource.lower(),
            action=permission_data.action.lower(),
        )

        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)

        logger.info(
            "Permission created",
            permission_id=str(permission.id),
            name=permission.name,
        )

        return permission

    async def delete_permission(self, permission_id: uuid.UUID) -> None:
        """Delete a permission.

        Args:
            permission_id: Permission ID to delete

        Raises:
            NotFoundException: If permission not found
        """
        permission = await self.get_by_id(permission_id)

        await self.db.delete(permission)

        logger.info(
            "Permission deleted",
            permission_id=str(permission_id),
            name=permission.name,
        )

    async def initialize_system_permissions(self) -> list[Permission]:
        """Initialize system permissions if they don't exist.

        Returns:
            List of created permissions
        """
        created = []

        for name, resource, action in self.SYSTEM_PERMISSIONS:
            existing = await self.get_by_name(name)
            if not existing:
                permission = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                )
                self.db.add(permission)
                created.append(permission)
                logger.info("System permission created", name=name)

        if created:
            await self.db.flush()

        return created

    async def check_permission_exists(
        self,
        resource: str,
        action: str,
    ) -> bool:
        """Check if a permission exists.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            True if permission exists
        """
        permission = await self.get_by_resource_action(resource, action)
        return permission is not None

    async def get_permissions_by_resources(
        self,
        resources: list[str],
    ) -> Sequence[Permission]:
        """Get all permissions for given resources.

        Args:
            resources: List of resource names

        Returns:
            List of permissions
        """
        resources_lower = [r.lower() for r in resources]
        result = await self.db.execute(
            select(Permission)
            .where(Permission.resource.in_(resources_lower))
        )
        return result.scalars().all()
