"""Tests for domain models.

This module contains unit tests for all domain models.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.permission import Permission
from app.domain.models.role import Role
from app.domain.models.user import User


@pytest.mark.unit
class TestUserModel:
    """Tests for User model."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is False

    async def test_user_full_name(self, db_session: AsyncSession):
        """Test user full_name property."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

        # Test with only first name
        user.last_name = None
        assert user.full_name == "John"

        # Test with only last name
        user.first_name = None
        user.last_name = "Doe"
        assert user.full_name == "Doe"

        # Test with neither
        user.first_name = None
        user.last_name = None
        assert user.full_name == "testuser"

    async def test_user_roles_relationship(self, db_session: AsyncSession):
        """Test user-roles relationship."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        role = Role(name="testrole", description="Test role")

        db_session.add(user)
        db_session.add(role)
        await db_session.commit()

        # Assign role to user
        user.roles.append(role)
        await db_session.commit()
        await db_session.refresh(user)

        assert len(user.roles) == 1
        assert user.roles[0].name == "testrole"

    async def test_has_role(self, db_session: AsyncSession):
        """Test has_role method."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        role = Role(name="admin", description="Admin role")

        db_session.add(user)
        db_session.add(role)
        await db_session.commit()

        user.roles.append(role)
        await db_session.commit()

        assert user.has_role("admin") is True
        assert user.has_role("user") is False

    async def test_is_superuser(self, db_session: AsyncSession):
        """Test is_superuser property."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        superuser_role = Role(name="superuser", description="Superuser")

        db_session.add(user)
        db_session.add(superuser_role)
        await db_session.commit()

        assert user.is_superuser is False

        user.roles.append(superuser_role)
        await db_session.commit()

        assert user.is_superuser is True

    async def test_has_permission(self, db_session: AsyncSession):
        """Test has_permission method."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        role = Role(name="admin", description="Admin")
        permission = Permission(name="users:read", resource="users", action="read")

        db_session.add(user)
        db_session.add(role)
        db_session.add(permission)
        await db_session.commit()

        role.permissions.append(permission)
        user.roles.append(role)
        await db_session.commit()

        assert user.has_permission("users", "read") is True
        assert user.has_permission("users", "delete") is False


@pytest.mark.unit
class TestRoleModel:
    """Tests for Role model."""

    async def test_create_role(self, db_session: AsyncSession):
        """Test creating a role."""
        role = Role(
            name="testrole",
            description="Test role description",
            is_default=False,
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        assert role.id is not None
        assert role.name == "testrole"
        assert role.description == "Test role description"
        assert role.is_default is False

    async def test_role_permissions_relationship(self, db_session: AsyncSession):
        """Test role-permissions relationship."""
        role = Role(name="admin", description="Admin role")
        permission1 = Permission(name="users:read", resource="users", action="read")
        permission2 = Permission(name="users:write", resource="users", action="write")

        db_session.add(role)
        db_session.add(permission1)
        db_session.add(permission2)
        await db_session.commit()

        role.permissions.append(permission1)
        role.permissions.append(permission2)
        await db_session.commit()
        await db_session.refresh(role)

        assert len(role.permissions) == 2

    async def test_has_permission_method(self, db_session: AsyncSession):
        """Test Role.has_permission method."""
        role = Role(name="admin", description="Admin")
        permission = Permission(name="users:read", resource="users", action="read")

        db_session.add(role)
        db_session.add(permission)
        await db_session.commit()

        role.permissions.append(permission)
        await db_session.commit()

        assert role.has_permission("users", "read") is True
        assert role.has_permission("users", "delete") is False


@pytest.mark.unit
class TestPermissionModel:
    """Tests for Permission model."""

    async def test_create_permission(self, db_session: AsyncSession):
        """Test creating a permission."""
        permission = Permission(
            name="users:read",
            resource="users",
            action="read",
        )
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)

        assert permission.id is not None
        assert permission.name == "users:read"
        assert permission.resource == "users"
        assert permission.action == "read"

    async def test_full_permission_property(self, db_session: AsyncSession):
        """Test full_permission property."""
        permission = Permission(
            name="users:read",
            resource="users",
            action="read",
        )
        assert permission.full_permission == "users:read"


@pytest.mark.unit
class TestModelTimestamps:
    """Tests for model timestamps."""

    async def test_user_timestamps(self, db_session: AsyncSession):
        """Test user created_at and updated_at."""
        from datetime import datetime

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
