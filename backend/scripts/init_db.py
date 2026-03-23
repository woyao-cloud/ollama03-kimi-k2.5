"""Database initialization script.

This script initializes the database with default data.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.permission_service import PermissionService
from app.application.services.role_service import RoleService
from app.config import settings
from app.infrastructure.database.session import AsyncSessionLocal
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


async def init_permissions(db: AsyncSession) -> None:
    """Initialize system permissions."""
    permission_service = PermissionService(db)
    created = await permission_service.initialize_system_permissions()
    logger.info(f"Initialized {len(created)} system permissions")


async def init_roles(db: AsyncSession) -> None:
    """Initialize default roles."""
    import uuid
    from app.domain.models.role import Role
    from app.domain.models.permission import Permission
    from sqlalchemy import select

    # Check if admin role exists
    result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        # Create admin role
        admin_role = Role(
            name="admin",
            description="Administrator with full access",
            is_default=False,
        )
        db.add(admin_role)
        await db.flush()

        # Assign all permissions to admin
        result = await db.execute(select(Permission))
        all_permissions = result.scalars().all()
        admin_role.permissions = list(all_permissions)

        logger.info("Created admin role with all permissions")

    # Check if user role exists
    result = await db.execute(select(Role).where(Role.name == "user"))
    user_role = result.scalar_one_or_none()

    if not user_role:
        # Create default user role
        user_role = Role(
            name="user",
            description="Standard user",
            is_default=True,
        )
        db.add(user_role)
        await db.flush()

        # Assign basic permissions
        result = await db.execute(
            select(Permission).where(Permission.name.in_([
                "users:read",
                "users:update",
            ]))
        )
        basic_permissions = result.scalars().all()
        user_role.permissions = list(basic_permissions)

        logger.info("Created user role with basic permissions")

    await db.commit()


async def main() -> None:
    """Main initialization function."""
    logger.info("Starting database initialization")

    async with AsyncSessionLocal() as db:
        try:
            # Initialize permissions
            await init_permissions(db)

            # Initialize roles
            await init_roles(db)

            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
