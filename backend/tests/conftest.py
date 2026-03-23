"""pytest configuration and fixtures.

This module provides test configuration and fixtures for the test suite.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import factory
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.security import hash_password
from app.domain.models.audit import AuditLog, LoginAttempt, UserSession
from app.domain.models.permission import Permission
from app.domain.models.role import Role
from app.domain.models.user import User
from app.infrastructure.database.base import Base
from app.main import app

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[None, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================
# Model Factories
# ============================================

class UserFactory(factory.Factory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyAttribute(lambda _: hash_password("TestPassword123!"))
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_verified = True


class RoleFactory(factory.Factory):
    """Factory for creating test roles."""

    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"role{n}")
    description = factory.Faker("sentence")
    is_default = False


class PermissionFactory(factory.Factory):
    """Factory for creating test permissions."""

    class Meta:
        model = Permission

    name = factory.Sequence(lambda n: f"resource{n}:action{n}")
    resource = factory.Sequence(lambda n: f"resource{n}")
    action = factory.Sequence(lambda n: f"action{n}")


# ============================================
# Test Data Fixtures
# ============================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = UserFactory()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = UserFactory(
        username="admin",
        email="admin@example.com",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    role = RoleFactory()
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_permission(db_session: AsyncSession) -> Permission:
    """Create a test permission."""
    permission = PermissionFactory()
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(permission)
    return permission


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Role:
    """Create an admin role with full permissions."""
    role = RoleFactory(
        name="admin",
        description="Administrator role",
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def user_role(db_session: AsyncSession) -> Role:
    """Create a standard user role."""
    role = RoleFactory(
        name="user",
        description="Standard user role",
        is_default=True,
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


# ============================================
# Auth Fixtures
# ============================================

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    from app.core.jwt import create_token_pair

    tokens = create_token_pair(
        user_id=test_user.id,
        roles=["user"],
        permissions=["users:read"],
    )

    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json",
    }


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, test_admin: User, admin_role: Role) -> dict:
    """Get authentication headers for admin user."""
    from app.core.jwt import create_token_pair

    # Assign admin role
    from app.application.services.user_service import UserService
    user_service = UserService(test_admin.roles[0].async_session if hasattr(test_admin, 'async_session') else None)

    tokens = create_token_pair(
        user_id=test_admin.id,
        roles=["admin", "superuser"],
        permissions=["*:*"],  # All permissions
    )

    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json",
    }


# ============================================
# Service Fixtures
# ============================================

@pytest_asyncio.fixture
def user_service(db_session: AsyncSession):
    """Create UserService instance."""
    from app.application.services.user_service import UserService
    return UserService(db_session)


@pytest_asyncio.fixture
def auth_service(db_session: AsyncSession):
    """Create AuthService instance."""
    from app.application.services.auth_service import AuthService
    return AuthService(db_session)


@pytest_asyncio.fixture
def role_service(db_session: AsyncSession):
    """Create RoleService instance."""
    from app.application.services.role_service import RoleService
    return RoleService(db_session)


@pytest_asyncio.fixture
def permission_service(db_session: AsyncSession):
    """Create PermissionService instance."""
    from app.application.services.permission_service import PermissionService
    return PermissionService(db_session)


@pytest_asyncio.fixture
def audit_service(db_session: AsyncSession):
    """Create AuditService instance."""
    from app.application.services.audit_service import AuditService
    return AuditService(db_session)
