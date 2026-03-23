"""Tests for permission and RBAC system.

This module contains tests for permission checking and role-based access control.
"""

import pytest

from app.core.permissions import (
    has_all_permissions,
    has_any_permission,
    has_permission,
    require_all_permissions,
    require_any_permission,
    require_permission,
)
from app.core.rbac import (
    has_all_roles,
    has_any_role,
    has_role,
    require_all_roles,
    require_any_role,
    require_role,
)


@pytest.mark.unit
class TestPermissionChecking:
    """Tests for permission checking functions."""

    def test_has_permission_exact_match(self):
        """Test checking exact permission match."""
        user_permissions = ["users:read", "users:write", "roles:read"]

        assert has_permission(user_permissions, "users", "read") is True
        assert has_permission(user_permissions, "users", "write") is True
        assert has_permission(user_permissions, "roles", "read") is True

    def test_has_permission_no_match(self):
        """Test checking permission without match."""
        user_permissions = ["users:read"]

        assert has_permission(user_permissions, "users", "delete") is False
        assert has_permission(user_permissions, "roles", "read") is False

    def test_has_permission_wildcard(self):
        """Test checking permission with wildcard."""
        user_permissions = ["users:*", "roles:read"]

        assert has_permission(user_permissions, "users", "read") is True
        assert has_permission(user_permissions, "users", "write") is True
        assert has_permission(user_permissions, "users", "delete") is True

    def test_has_permission_superuser(self):
        """Test checking permission with superuser."""
        user_permissions = ["*:*"]

        assert has_permission(user_permissions, "any", "action") is True

    def test_has_permission_case_insensitive(self):
        """Test permission checking is case insensitive."""
        user_permissions = ["Users:Read"]

        assert has_permission(user_permissions, "users", "read") is True
        assert has_permission(user_permissions, "USERS", "READ") is True


@pytest.mark.unit
class TestAnyPermission:
    """Tests for has_any_permission function."""

    def test_has_any_permission_with_match(self):
        """Test checking any permission with match."""
        user_permissions = ["users:read", "roles:read"]
        required = [("users", "write"), ("users", "read")]

        assert has_any_permission(user_permissions, required) is True

    def test_has_any_permission_no_match(self):
        """Test checking any permission without match."""
        user_permissions = ["users:read"]
        required = [("users", "write"), ("users", "delete")]

        assert has_any_permission(user_permissions, required) is False


@pytest.mark.unit
class TestAllPermissions:
    """Tests for has_all_permissions function."""

    def test_has_all_permissions_with_all(self):
        """Test checking all permissions with all present."""
        user_permissions = ["users:read", "users:write", "users:delete"]
        required = [("users", "read"), ("users", "write")]

        assert has_all_permissions(user_permissions, required) is True

    def test_has_all_permissions_missing_one(self):
        """Test checking all permissions missing one."""
        user_permissions = ["users:read", "users:write"]
        required = [("users", "read"), ("users", "delete")]

        assert has_all_permissions(user_permissions, required) is False


@pytest.mark.unit
class TestRoleChecking:
    """Tests for role checking functions."""

    def test_has_role_exact_match(self):
        """Test checking exact role match."""
        user_roles = ["admin", "user"]

        assert has_role(user_roles, "admin") is True
        assert has_role(user_roles, "user") is True
        assert has_role(user_roles, "moderator") is False

    def test_has_role_superuser(self):
        """Test checking role with superuser."""
        user_roles = ["superuser"]

        assert has_role(user_roles, "admin") is True
        assert has_role(user_roles, "any_role") is True

    def test_has_role_case_insensitive(self):
        """Test role checking is case insensitive."""
        user_roles = ["Admin"]

        assert has_role(user_roles, "admin") is True
        assert has_role(user_roles, "ADMIN") is True


@pytest.mark.unit
class TestAnyRole:
    """Tests for has_any_role function."""

    def test_has_any_role_with_match(self):
        """Test checking any role with match."""
        user_roles = ["user"]
        required = ["admin", "user"]

        assert has_any_role(user_roles, required) is True

    def test_has_any_role_no_match(self):
        """Test checking any role without match."""
        user_roles = ["user"]
        required = ["admin", "moderator"]

        assert has_any_role(user_roles, required) is False


@pytest.mark.unit
class TestAllRoles:
    """Tests for has_all_roles function."""

    def test_has_all_roles_with_all(self):
        """Test checking all roles with all present."""
        user_roles = ["admin", "moderator", "user"]
        required = ["admin", "moderator"]

        assert has_all_roles(user_roles, required) is True

    def test_has_all_roles_missing_one(self):
        """Test checking all roles missing one."""
        user_roles = ["admin"]
        required = ["admin", "moderator"]

        assert has_all_roles(user_roles, required) is False


@pytest.mark.unit
class TestPermissionDecorators:
    """Tests for permission decorator factories."""

    def test_require_permission_factory(self):
        """Test require_permission decorator factory."""
        decorator = require_permission("users", "read")
        assert callable(decorator)

    def test_require_any_permission_factory(self):
        """Test require_any_permission decorator factory."""
        decorator = require_any_permission(("users", "read"), ("roles", "read"))
        assert callable(decorator)

    def test_require_all_permissions_factory(self):
        """Test require_all_permissions decorator factory."""
        decorator = require_all_permissions(("users", "read"), ("users", "write"))
        assert callable(decorator)


@pytest.mark.unit
class TestRoleDecorators:
    """Tests for role decorator factories."""

    def test_require_role_factory(self):
        """Test require_role decorator factory."""
        decorator = require_role("admin")
        assert callable(decorator)

    def test_require_any_role_factory(self):
        """Test require_any_role decorator factory."""
        decorator = require_any_role("admin", "moderator")
        assert callable(decorator)

    def test_require_all_roles_factory(self):
        """Test require_all_roles decorator factory."""
        decorator = require_all_roles("admin", "moderator")
        assert callable(decorator)
