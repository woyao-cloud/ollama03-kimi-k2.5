"""Integration tests for API endpoints.

This module contains integration tests for all API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


@pytest.mark.integration
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser123",
                "email": "test123@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser123"
        assert data["email"] == "test123@example.com"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registering with duplicate username."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "dup1@example.com",
                "password": "TestPassword123!",
            },
        )

        # Second registration with same username
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "dup2@example.com",
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registering with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "weakpass",
                "email": "weak@example.com",
                "password": "123",
            },
        )

        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register a user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "TestPassword123!",
            },
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest",
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert "user" in data

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login with missing credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "password": "password",
            },
        )

        assert response.status_code == 401

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient):
        """Test getting current user with authentication."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "metest",
                "email": "me@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "metest",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Get me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "metest"
        assert data["email"] == "me@example.com"

    async def test_refresh_token(self, client: AsyncClient):
        """Test refreshing token."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "refreshtest",
                "email": "refresh@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "refreshtest",
                "password": "TestPassword123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_logout(self, client: AsyncClient):
        """Test logout."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "logouttest",
                "email": "logout@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "logouttest",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestUserEndpoints:
    """Tests for user management endpoints."""

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        """Test listing users without authentication."""
        response = await client.get("/api/v1/users")

        assert response.status_code == 401

    async def test_list_users_no_permission(self, client: AsyncClient):
        """Test listing users without permission."""
        # Register and login as regular user
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "regular",
                "email": "regular@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "regular",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Try to list users
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_get_user(self, client: AsyncClient):
        """Test getting a specific user."""
        # Register
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "getusertest",
                "email": "getuser@example.com",
                "password": "TestPassword123!",
            },
        )
        user_id = reg_response.json()["id"]

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "getusertest",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Get own user data
        response = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "getusertest"

    async def test_update_user(self, client: AsyncClient):
        """Test updating a user."""
        # Register
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "updatetest",
                "email": "update@example.com",
                "password": "TestPassword123!",
            },
        )
        user_id = reg_response.json()["id"]

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "updatetest",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Update user
        response = await client.put(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"


@pytest.mark.integration
class TestRoleEndpoints:
    """Tests for role management endpoints."""

    async def test_list_roles_unauthenticated(self, client: AsyncClient):
        """Test listing roles without authentication."""
        response = await client.get("/api/v1/roles")

        assert response.status_code == 401

    async def test_create_role_no_permission(self, client: AsyncClient):
        """Test creating role without permission."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "norole",
                "email": "norole@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "norole",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Try to create role
        response = await client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "newrole",
                "description": "Test role",
            },
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestPermissionEndpoints:
    """Tests for permission endpoints."""

    async def test_check_permission(self, client: AsyncClient):
        """Test checking permission."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "permtest",
                "email": "perm@example.com",
                "password": "TestPassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "permtest",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Check permission
        response = await client.post(
            "/api/v1/permissions/check",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "resource": "users",
                "action": "read",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "has_permission" in data


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling."""

    async def test_404_not_found(self, client: AsyncClient):
        """Test 404 response."""
        response = await client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    async def test_422_validation_error(self, client: AsyncClient):
        """Test validation error response."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Too short
                "email": "invalid-email",
                "password": "123",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    async def test_method_not_allowed(self, client: AsyncClient):
        """Test method not allowed."""
        response = await client.delete("/api/v1/auth/login")

        assert response.status_code == 405

    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers."""
        response = await client.options("/api/v1/auth/login")

        assert "access-control-allow-origin" in response.headers
