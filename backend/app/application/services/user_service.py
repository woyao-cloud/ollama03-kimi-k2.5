"""User service module.

This module provides business logic for user management operations.
"""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.domain.models.role import Role
from app.domain.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User model instance

        Raises:
            NotFoundException: If user not found
        """
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("User not found", user_id=str(user_id))
            raise NotFoundException("User", str(user_id))

        return user

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User model instance or None
        """
        result = await self.db.execute(
            select(User)
            .where(User.username == username)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: Email address

        Returns:
            User model instance or None
        """
        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, username_or_email: str) -> User | None:
        """Get user by username or email.

        Args:
            username_or_email: Username or email

        Returns:
            User model instance or None
        """
        # Try username first
        user = await self.get_by_username(username_or_email)
        if user:
            return user

        # Try email
        return await self.get_by_email(username_or_email)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        is_verified: bool | None = None,
    ) -> tuple[Sequence[User], int]:
        """List users with optional filtering.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            is_active: Filter by active status
            is_verified: Filter by verified status

        Returns:
            Tuple of (users list, total count)
        """
        # Build query
        query = select(User).options(selectinload(User.roles))

        # Apply filters
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        # Get total count
        count_query = select(select(User.id).subquery().c.id)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)
        if is_verified is not None:
            count_query = count_query.where(User.is_verified == is_verified)

        total_result = await self.db.execute(count_query)
        total = len(total_result.all())

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user model

        Raises:
            ConflictException: If username or email already exists
        """
        # Check for existing username
        existing_user = await self.get_by_username(user_data.username)
        if existing_user:
            raise ConflictException(
                f"Username '{user_data.username}' is already taken",
                field="username",
            )

        # Check for existing email
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise ConflictException(
                f"Email '{user_data.email}' is already registered",
                field="email",
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True,
            is_verified=False,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "User created",
            user_id=str(user.id),
            username=user.username,
        )

        return user

    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        """Update an existing user.

        Args:
            user_id: User ID to update
            user_data: User update data

        Returns:
            Updated user model

        Raises:
            NotFoundException: If user not found
            ConflictException: If new username or email already exists
        """
        user = await self.get_by_id(user_id)

        # Check username uniqueness if updating
        if user_data.username and user_data.username != user.username:
            existing = await self.get_by_username(user_data.username)
            if existing:
                raise ConflictException(
                    f"Username '{user_data.username}' is already taken",
                    field="username",
                )
            user.username = user_data.username

        # Check email uniqueness if updating
        if user_data.email and user_data.email != user.email:
            existing = await self.get_by_email(user_data.email)
            if existing:
                raise ConflictException(
                    f"Email '{user_data.email}' is already registered",
                    field="email",
                )
            user.email = user_data.email

        # Update other fields
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.is_verified is not None:
            user.is_verified = user_data.is_verified

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "User updated",
            user_id=str(user.id),
            username=user.username,
        )

        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user.

        Args:
            user_id: User ID to delete

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)

        await self.db.delete(user)

        logger.info(
            "User deleted",
            user_id=str(user_id),
            username=user.username,
        )

    async def update_password(self, user_id: uuid.UUID, new_password: str) -> User:
        """Update user password.

        Args:
            user_id: User ID
            new_password: New plain text password

        Returns:
            Updated user model

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)

        # Hash and set new password
        user.password_hash = hash_password(new_password)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "User password updated",
            user_id=str(user_id),
        )

        return user

    async def verify_password(self, user_id: uuid.UUID, password: str) -> bool:
        """Verify user password.

        Args:
            user_id: User ID
            password: Plain text password to verify

        Returns:
            True if password matches

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)
        return verify_password(password, user.password_hash)

    async def assign_roles(self, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> User:
        """Assign roles to a user.

        Args:
            user_id: User ID
            role_ids: List of role IDs to assign

        Returns:
            Updated user model

        Raises:
            NotFoundException: If user or any role not found
        """
        user = await self.get_by_id(user_id)

        # Fetch roles
        from sqlalchemy import select
        result = await self.db.execute(
            select(Role).where(Role.id.in_(role_ids))
        )
        roles = result.scalars().all()

        # Check all roles exist
        found_ids = {role.id for role in roles}
        missing_ids = set(role_ids) - found_ids
        if missing_ids:
            raise NotFoundException("Role", str(list(missing_ids)[0]))

        # Assign roles
        user.roles = list(roles)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "Roles assigned to user",
            user_id=str(user_id),
            role_ids=[str(rid) for rid in role_ids],
        )

        return user

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        """Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID to remove

        Returns:
            Updated user model
        """
        user = await self.get_by_id(user_id)

        # Filter out the role
        user.roles = [role for role in user.roles if role.id != role_id]

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "Role removed from user",
            user_id=str(user_id),
            role_id=str(role_id),
        )

        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        from datetime import datetime, timezone

        user = await self.get_by_id(user_id)
        user.last_login_at = datetime.now(timezone.utc)

        await self.db.flush()

        logger.debug(
            "User last login updated",
            user_id=str(user_id),
        )
