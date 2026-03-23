"""Tests for application services.

This module contains unit tests for all application services.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.user_service import UserService
from app.core.exceptions import ConflictException, NotFoundException
from app.domain.models.role import Role
from app.domain.models.user import User
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.unit
class TestUserService:
    """Tests for UserService."""

    async def test_create_user(self, db_session: AsyncSession, user_service: UserService):
        """Test creating a user."""
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="TestPassword123!",
            first_name="New",
            last_name="User",
        )

        user = await user_service.create_user(user_data)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.password_hash != "TestPassword123!"  # Password should be hashed

    async def test_create_user_duplicate_username(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test creating user with duplicate username."""
        user_data = UserCreate(
            username=test_user.username,
            email="different@example.com",
            password="TestPassword123!",
        )

        with pytest.raises(ConflictException) as exc_info:
            await user_service.create_user(user_data)

        assert "username" in str(exc_info.value).lower()

    async def test_create_user_duplicate_email(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test creating user with duplicate email."""
        user_data = UserCreate(
            username="different",
            email=test_user.email,
            password="TestPassword123!",
        )

        with pytest.raises(ConflictException) as exc_info:
            await user_service.create_user(user_data)

        assert "email" in str(exc_info.value).lower()

    async def test_get_user_by_id(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test getting user by ID."""
        user = await user_service.get_by_id(test_user.id)

        assert user.id == test_user.id
        assert user.username == test_user.username

    async def test_get_user_by_id_not_found(self, db_session: AsyncSession, user_service: UserService):
        """Test getting non-existent user."""
        fake_id = uuid.uuid4()

        with pytest.raises(NotFoundException) as exc_info:
            await user_service.get_by_id(fake_id)

        assert "user" in str(exc_info.value).lower()

    async def test_get_user_by_username(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test getting user by username."""
        user = await user_service.get_by_username(test_user.username)

        assert user is not None
        assert user.username == test_user.username

    async def test_get_user_by_email(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test getting user by email."""
        user = await user_service.get_by_email(test_user.email)

        assert user is not None
        assert user.email == test_user.email

    async def test_update_user(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test updating user."""
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
        )

        updated = await user_service.update_user(test_user.id, update_data)

        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"
        assert updated.username == test_user.username  # Unchanged

    async def test_delete_user(
        self, db_session: AsyncSession, user_service: UserService
    ):
        """Test deleting user."""
        # Create a user to delete
        user = User(
            username="todelete",
            email="delete@example.com",
            password_hash="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        # Delete the user
        await user_service.delete_user(user.id)

        # Verify user is deleted
        with pytest.raises(NotFoundException):
            await user_service.get_by_id(user.id)

    async def test_update_password(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test updating password."""
        new_password = "NewPassword123!"
        old_hash = test_user.password_hash

        updated = await user_service.update_password(test_user.id, new_password)

        assert updated.password_hash != old_hash
        assert updated.password_hash != new_password  # Should be hashed

    async def test_list_users(
        self, db_session: AsyncSession, user_service: UserService
    ):
        """Test listing users."""
        # Create some users
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash="hashed",
            )
            db_session.add(user)
        await db_session.commit()

        users, total = await user_service.list_users(skip=0, limit=10)

        assert len(users) >= 5
        assert total >= 5

    async def test_list_users_with_filter(
        self, db_session: AsyncSession, user_service: UserService
    ):
        """Test listing users with filters."""
        # Create active and inactive users
        active_user = User(
            username="active",
            email="active@example.com",
            password_hash="hashed",
            is_active=True,
        )
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash="hashed",
            is_active=False,
        )
        db_session.add(active_user)
        db_session.add(inactive_user)
        await db_session.commit()

        active_users, total = await user_service.list_users(
            skip=0, limit=10, is_active=True
        )

        assert all(u.is_active for u in active_users)

    async def test_assign_roles(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test assigning roles to user."""
        role1 = Role(name="role1", description="Role 1")
        role2 = Role(name="role2", description="Role 2")
        db_session.add(role1)
        db_session.add(role2)
        await db_session.commit()

        user = await user_service.assign_roles(test_user.id, [role1.id, role2.id])

        assert len(user.roles) == 2

    async def test_verify_password(
        self, db_session: AsyncSession, user_service: UserService, test_user: User
    ):
        """Test password verification."""
        # The test user has password "TestPassword123!" from factory
        is_valid = await user_service.verify_password(test_user.id, "TestPassword123!")
        assert is_valid is True

        is_invalid = await user_service.verify_password(test_user.id, "wrongpassword")
        assert is_invalid is False


@pytest.mark.unit
class TestRoleService:
    """Tests for RoleService."""

    async def test_create_role(self, db_session: AsyncSession, role_service):
        """Test creating a role."""
        from app.schemas.role import RoleCreate

        role_data = RoleCreate(
            name="newrole",
            description="New role",
        )

        role = await role_service.create_role(role_data)

        assert role.id is not None
        assert role.name == "newrole"

    async def test_create_role_duplicate(
        self, db_session: AsyncSession, role_service, test_role: Role
    ):
        """Test creating duplicate role."""
        from app.schemas.role import RoleCreate

        role_data = RoleCreate(
            name=test_role.name,
            description="Duplicate",
        )

        with pytest.raises(ConflictException):
            await role_service.create_role(role_data)

    async def test_get_role_by_id(
        self, db_session: AsyncSession, role_service, test_role: Role
    ):
        """Test getting role by ID."""
        role = await role_service.get_by_id(test_role.id)

        assert role.id == test_role.id
        assert role.name == test_role.name

    async def test_delete_role(
        self, db_session: AsyncSession, role_service
    ):
        """Test deleting role."""
        role = Role(name="todelete", description="To delete")
        db_session.add(role)
        await db_session.commit()

        await role_service.delete_role(role.id)

        with pytest.raises(NotFoundException):
            await role_service.get_by_id(role.id)


@pytest.mark.unit
class TestPermissionService:
    """Tests for PermissionService."""

    async def test_create_permission(self, db_session: AsyncSession, permission_service):
        """Test creating a permission."""
        from app.schemas.permission import PermissionCreate

        perm_data = PermissionCreate(
            name="test:read",
            resource="test",
            action="read",
        )

        perm = await permission_service.create_permission(perm_data)

        assert perm.id is not None
        assert perm.name == "test:read"

    async def test_create_permission_duplicate(
        self, db_session: AsyncSession, permission_service, test_permission: Permission
    ):
        """Test creating duplicate permission."""
        from app.schemas.permission import PermissionCreate

        perm_data = PermissionCreate(
            name=test_permission.name,
            resource="test",
            action="test",
        )

        with pytest.raises(ConflictException):
            await permission_service.create_permission(perm_data)

    async def test_get_permission_by_id(
        self, db_session: AsyncSession, permission_service, test_permission: Permission
    ):
        """Test getting permission by ID."""
        perm = await permission_service.get_by_id(test_permission.id)

        assert perm.id == test_permission.id

    async def test_initialize_system_permissions(self, db_session: AsyncSession, permission_service):
        """Test initializing system permissions."""
        created = await permission_service.initialize_system_permissions()

        assert len(created) > 0

        # Run again - should not create duplicates
        created_again = await permission_service.initialize_system_permissions()
        assert len(created_again) == 0
