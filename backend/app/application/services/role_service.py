"""Role service module.

This module provides business logic for role management operations.
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.domain.models.permission import Permission
from app.domain.models.role import Role
from app.domain.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate

logger = get_logger(__name__)


class RoleService:
    """Service for role management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_id(self, role_id: uuid.UUID) -> Role:
        """Get role by ID.

        Args:
            role_id: Role UUID

        Returns:
            Role model instance

        Raises:
            NotFoundException: If role not found
        """
        result = await self.db.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if not role:
            logger.warning("Role not found", role_id=str(role_id))
            raise NotFoundException("Role", str(role_id))

        return role

    async def get_by_name(self, name: str) -> Role | None:
        """Get role by name.

        Args:
            name: Role name

        Returns:
            Role model instance or None
        """
        result = await self.db.execute(
            select(Role)
            .where(Role.name == name.lower())
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_default_role(self) -> Role | None:
        """Get the default role for new users.

        Returns:
            Default role or None if not set
        """
        result = await self.db.execute(
            select(Role)
            .where(Role.is_default == True)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def list_roles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Role], int]:
        """List all roles.

        Args:
            skip: Number of roles to skip
            limit: Maximum number of roles to return

        Returns:
            Tuple of (roles list, total count)
        """
        # Get total count
        count_result = await self.db.execute(select(Role.id))
        total = len(count_result.all())

        # Get roles with permissions
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .offset(skip)
            .limit(limit)
        )
        roles = result.scalars().all()

        return list(roles), total

    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            role_data: Role creation data

        Returns:
            Created role model

        Raises:
            ConflictException: If role name already exists
        """
        # Check for existing role
        existing = await self.get_by_name(role_data.name)
        if existing:
            raise ConflictException(
                f"Role '{role_data.name}' already exists",
                field="name",
            )

        # Create role
        role = Role(
            name=role_data.name.lower(),
            description=role_data.description,
            is_default=role_data.is_default,
        )

        # Handle default role
        if role_data.is_default:
            # Unset any existing default role
            await self._unset_default_roles()

        # Add permissions if specified
        if role_data.permission_ids:
            permissions_result = await self.db.execute(
                select(Permission).where(Permission.id.in_(role_data.permission_ids))
            )
            permissions = permissions_result.scalars().all()

            # Verify all permissions exist
            found_ids = {p.id for p in permissions}
            missing_ids = set(role_data.permission_ids) - found_ids
            if missing_ids:
                raise NotFoundException(
                    "Permission",
                    str(list(missing_ids)[0]),
                )

            role.permissions = list(permissions)

        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)

        logger.info(
            "Role created",
            role_id=str(role.id),
            name=role.name,
        )

        return role

    async def update_role(self, role_id: uuid.UUID, role_data: RoleUpdate) -> Role:
        """Update an existing role.

        Args:
            role_id: Role ID to update
            role_data: Role update data

        Returns:
            Updated role model

        Raises:
            NotFoundException: If role not found
            ConflictException: If new name already exists
        """
        role = await self.get_by_id(role_id)

        # Check name uniqueness if updating
        if role_data.name and role_data.name != role.name:
            existing = await self.get_by_name(role_data.name)
            if existing:
                raise ConflictException(
                    f"Role '{role_data.name}' already exists",
                    field="name",
                )
            role.name = role_data.name.lower()

        # Update description
        if role_data.description is not None:
            role.description = role_data.description

        # Handle default role change
        if role_data.is_default is not None:
            if role_data.is_default and not role.is_default:
                await self._unset_default_roles()
            role.is_default = role_data.is_default

        # Update permissions if specified
        if role_data.permission_ids is not None:
            permissions_result = await self.db.execute(
                select(Permission).where(Permission.id.in_(role_data.permission_ids))
            )
            permissions = permissions_result.scalars().all()

            # Verify all permissions exist
            found_ids = {p.id for p in permissions}
            missing_ids = set(role_data.permission_ids) - found_ids
            if missing_ids:
                raise NotFoundException(
                    "Permission",
                    str(list(missing_ids)[0]),
                )

            role.permissions = list(permissions)

        await self.db.flush()
        await self.db.refresh(role)

        logger.info(
            "Role updated",
            role_id=str(role.id),
            name=role.name,
        )

        return role

    async def delete_role(self, role_id: uuid.UUID) -> None:
        """Delete a role.

        Args:
            role_id: Role ID to delete

        Raises:
            NotFoundException: If role not found
        """
        role = await self.get_by_id(role_id)

        await self.db.delete(role)

        logger.info(
            "Role deleted",
            role_id=str(role_id),
            name=role.name,
        )

    async def assign_permissions(
        self,
        role_id: uuid.UUID,
        permission_ids: list[uuid.UUID],
    ) -> Role:
        """Assign permissions to a role.

        Args:
            role_id: Role ID
            permission_ids: List of permission IDs to assign

        Returns:
            Updated role model
        """
        role = await self.get_by_id(role_id)

        # Fetch permissions
        result = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )
        permissions = result.scalars().all()

        # Check all permissions exist
        found_ids = {p.id for p in permissions}
        missing_ids = set(permission_ids) - found_ids
        if missing_ids:
            raise NotFoundException(
                "Permission",
                str(list(missing_ids)[0]),
            )

        # Add new permissions (avoid duplicates)
        existing_ids = {p.id for p in role.permissions}
        for permission in permissions:
            if permission.id not in existing_ids:
                role.permissions.append(permission)

        await self.db.flush()
        await self.db.refresh(role)

        logger.info(
            "Permissions assigned to role",
            role_id=str(role_id),
            permission_ids=[str(pid) for pid in permission_ids],
        )

        return role

    async def remove_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Role:
        """Remove a permission from a role.

        Args:
            role_id: Role ID
            permission_id: Permission ID to remove

        Returns:
            Updated role model
        """
        role = await self.get_by_id(role_id)

        # Filter out the permission
        role.permissions = [
            p for p in role.permissions if p.id != permission_id
        ]

        await self.db.flush()
        await self.db.refresh(role)

        logger.info(
            "Permission removed from role",
            role_id=str(role_id),
            permission_id=str(permission_id),
        )

        return role

    async def _unset_default_roles(self) -> None:
        """Unset all default roles."""
        result = await self.db.execute(
            select(Role).where(Role.is_default == True)
        )
        default_roles = result.scalars().all()

        for role in default_roles:
            role.is_default = False

        await self.db.flush()
