"""Authentication service module.

This module provides business logic for authentication operations.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from app.core.jwt import create_token_pair, verify_token
from app.core.logging import get_logger
from app.core.security import verify_password
from app.domain.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    TokenResponse,
)
from app.application.services.user_service import UserService

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.user_service = UserService(db)

    async def authenticate(self, credentials: LoginRequest) -> User:
        """Authenticate a user with username/email and password.

        Args:
            credentials: Login credentials

        Returns:
            Authenticated user

        Raises:
            AuthenticationException: If credentials are invalid
            ValidationException: If neither username nor email is provided
        """
        # Validate credentials
        if not credentials.username and not credentials.email:
            raise ValidationException(
                "Either username or email must be provided",
                field="username",
            )

        # Get username/email to search
        username_or_email = credentials.username or credentials.email

        # Find user
        user = await self.user_service.get_by_username_or_email(username_or_email)
        if not user:
            logger.warning(
                "Authentication failed: user not found",
                identifier=username_or_email,
            )
            raise AuthenticationException("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            logger.warning(
                "Authentication failed: user is inactive",
                user_id=str(user.id),
            )
            raise AuthenticationException("Account is deactivated")

        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            logger.warning(
                "Authentication failed: invalid password",
                user_id=str(user.id),
            )
            raise AuthenticationException("Invalid credentials")

        logger.info(
            "User authenticated",
            user_id=str(user.id),
            username=user.username,
        )

        return user

    async def login(self, credentials: LoginRequest) -> AuthResponse:
        """Login user and generate tokens.

        Args:
            credentials: Login credentials

        Returns:
            Authentication response with tokens and user data
        """
        # Authenticate user
        user = await self.authenticate(credentials)

        # Update last login
        await self.user_service.update_last_login(user.id)

        # Generate tokens
        tokens = self._generate_token_response(user)

        # TODO: Create user session in database

        logger.info(
            "User logged in",
            user_id=str(user.id),
        )

        return AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "roles": [role.name for role in user.roles],
            },
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            AuthenticationException: If refresh token is invalid
        """
        try:
            # Verify refresh token
            payload = verify_token(refresh_token, token_type="refresh")

            # Get user
            user = await self.user_service.get_by_id(payload.sub)

            # Check if user is active
            if not user.is_active:
                raise AuthenticationException("Account is deactivated")

            # Generate new tokens
            tokens = self._generate_token_response(user)

            # TODO: Revoke old refresh token and create new session

            logger.info(
                "Token refreshed",
                user_id=str(user.id),
            )

            return TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=tokens["expires_in"],
                refresh_expires_in=tokens["refresh_expires_in"],
            )

        except Exception as e:
            logger.warning("Token refresh failed", error=str(e))
            raise AuthenticationException("Invalid refresh token")

    async def logout(self, user_id: uuid.UUID, refresh_token: str | None = None) -> None:
        """Logout user.

        Args:
            user_id: User ID
            refresh_token: Optional refresh token to revoke
        """
        # TODO: Revoke refresh token session from database

        logger.info(
            "User logged out",
            user_id=str(user_id),
        )

    async def logout_all_sessions(self, user_id: uuid.UUID) -> None:
        """Logout user from all sessions.

        Args:
            user_id: User ID
        """
        # TODO: Revoke all sessions for user from database

        logger.info(
            "User logged out from all sessions",
            user_id=str(user_id),
        )

    async def get_current_user(self, token: str) -> User:
        """Get current user from access token.

        Args:
            token: Access token

        Returns:
            Current user

        Raises:
            AuthenticationException: If token is invalid
        """
        try:
            # Verify token
            payload = verify_token(token, token_type="access")

            # Get user
            user = await self.user_service.get_by_id(payload.sub)

            # Check if user is active
            if not user.is_active:
                raise AuthenticationException("Account is deactivated")

            return user

        except NotFoundException:
            raise AuthenticationException("User not found")
        except Exception as e:
            logger.warning("Failed to get current user", error=str(e))
            raise AuthenticationException("Invalid token")

    def _generate_token_response(self, user: User) -> dict:
        """Generate token response for a user.

        Args:
            user: User model

        Returns:
            Token dictionary
        """
        # Get role names
        roles = [role.name for role in user.roles]

        # Get permissions from roles
        permissions = []
        for role in user.roles:
            for permission in role.permissions:
                permissions.append(permission.full_permission)

        # Create token pair
        return create_token_pair(
            user_id=user.id,
            roles=roles,
            permissions=permissions,
        )

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Raises:
            AuthenticationException: If current password is incorrect
        """
        # Verify current password
        is_valid = await self.user_service.verify_password(user_id, current_password)
        if not is_valid:
            raise AuthenticationException("Current password is incorrect")

        # Update password
        await self.user_service.update_password(user_id, new_password)

        # TODO: Revoke all sessions to force re-login

        logger.info(
            "User password changed",
            user_id=str(user_id),
        )

    async def request_password_reset(self, email: str) -> None:
        """Request password reset for user.

        Args:
            email: User email

        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_service.get_by_email(email)
        if not user:
            raise NotFoundException("User", email)

        # TODO: Generate reset token and send email

        logger.info(
            "Password reset requested",
            user_id=str(user.id),
            email=email,
        )

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """Confirm password reset with token.

        Args:
            token: Reset token
            new_password: New password

        Raises:
            AuthenticationException: If token is invalid
        """
        # TODO: Verify reset token and update password

        logger.info("Password reset confirmed")

    async def verify_email(self, token: str) -> None:
        """Verify user email with token.

        Args:
            token: Verification token

        Raises:
            AuthenticationException: If token is invalid
        """
        # TODO: Verify email token and mark user as verified

        logger.info("Email verified")
