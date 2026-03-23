"""Authentication endpoints.

This module provides authentication-related API endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    AuthServiceDep,
    UserServiceDep,
    get_client_ip,
    get_user_agent,
)
from app.core.auth import get_current_user, oauth2_scheme
from app.core.exceptions import AuthenticationException, ValidationException
from app.core.lockout import lockout_service
from app.core.logging import get_logger
from app.core.rate_limit import login_rate_limit
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_service: AuthServiceDep,
) -> AuthResponse:
    """Authenticate user and return access tokens.

    Args:
        request: FastAPI request
        credentials: Login credentials (username/email + password)
        auth_service: Authentication service

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If credentials are invalid or account is locked
    """
    # Get client info for logging
    ip_address = await get_client_ip(request)
    user_agent = await get_user_agent(request)

    # Check account lockout
    identifier = credentials.username or credentials.email
    if lockout_service.is_locked(identifier, ip_address):
        lockout_info = lockout_service.get_lockout_info(identifier, ip_address)
        logger.warning(
            "Login attempt on locked account",
            identifier=identifier,
            ip_address=ip_address,
        )
        raise AuthenticationException(
            f"Account is temporarily locked. Try again in {lockout_info['remaining_minutes']} minutes."
        )

    try:
        # Attempt login
        response = await auth_service.login(credentials)

        # Record successful login and clear lockout
        lockout_service.record_successful_login(identifier, ip_address)

        logger.info(
            "User logged in successfully",
            user_id=response.user.get("id"),
            ip_address=ip_address,
        )

        return response

    except AuthenticationException as e:
        # Record failed attempt
        lockout_service.record_failed_attempt(identifier, ip_address)
        remaining = lockout_service.get_remaining_attempts(identifier, ip_address)

        logger.warning(
            "Login failed",
            identifier=identifier,
            ip_address=ip_address,
            remaining_attempts=remaining,
        )

        # Add warning if close to lockout
        if remaining <= 2:
            raise AuthenticationException(
                f"{str(e)}. {remaining} attempts remaining before account lockout."
            )
        raise


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """Register a new user.

    Args:
        request: FastAPI request
        user_data: User creation data
        user_service: User service

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    ip_address = await get_client_ip(request)

    # Create user
    user = await user_service.create_user(user_data)

    logger.info(
        "User registered",
        user_id=str(user.id),
        username=user.username,
        ip_address=ip_address,
    )

    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        auth_service: Authentication service

    Returns:
        New token response

    Raises:
        HTTPException: If refresh token is invalid
    """
    return await auth_service.refresh_token(refresh_data.refresh_token)


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: Annotated[dict, Depends(get_current_user)],
    user_service: UserServiceDep,
) -> dict:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token
        user_service: User service

    Returns:
        User information
    """
    # Fetch fresh user data
    import uuid
    user = await user_service.get_by_id(uuid.UUID(current_user["id"]))

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "roles": [role.name for role in user.roles],
        "permissions": [
            f"{p.resource}:{p.action}"
            for role in user.roles
            for p in role.permissions
        ],
    }


@router.post("/logout")
async def logout(
    request: Request,
    logout_data: LogoutRequest | None = None,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    auth_service: AuthServiceDep = None,
) -> dict:
    """Logout user.

    Args:
        request: FastAPI request
        logout_data: Optional logout data
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Success message
    """
    import uuid

    user_id = uuid.UUID(current_user["id"])

    if logout_data and logout_data.all_sessions:
        await auth_service.logout_all_sessions(user_id)
        message = "Logged out from all sessions"
    else:
        refresh_token = logout_data.refresh_token if logout_data else None
        await auth_service.logout(user_id, refresh_token)
        message = "Logged out successfully"

    logger.info(
        "User logged out",
        user_id=str(user_id),
        all_sessions=logout_data.all_sessions if logout_data else False,
    )

    return {"message": message}


@router.post("/password-reset-request")
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    auth_service: AuthServiceDep,
) -> dict:
    """Request password reset.

    Args:
        request: FastAPI request
        reset_request: Password reset request
        auth_service: Authentication service

    Returns:
        Success message (always returns same message for security)
    """
    ip_address = await get_client_ip(request)

    try:
        await auth_service.request_password_reset(reset_request.email)
    except Exception:
        # Don't reveal if email exists
        pass

    logger.info(
        "Password reset requested",
        email=reset_request.email,
        ip_address=ip_address,
    )

    return {
        "message": "If an account with this email exists, a password reset link has been sent."
    }


@router.post("/password-reset-confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthServiceDep,
) -> dict:
    """Confirm password reset with token.

    Args:
        reset_data: Password reset confirmation data
        auth_service: Authentication service

    Returns:
        Success message
    """
    await auth_service.confirm_password_reset(
        reset_data.token,
        reset_data.new_password,
    )

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    auth_service: AuthServiceDep,
) -> dict:
    """Change user password.

    Args:
        request: FastAPI request
        current_password: Current password
        new_password: New password
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Success message
    """
    import uuid

    user_id = uuid.UUID(current_user["id"])
    ip_address = await get_client_ip(request)

    await auth_service.change_password(user_id, current_password, new_password)

    logger.info(
        "Password changed",
        user_id=str(user_id),
        ip_address=ip_address,
    )

    return {"message": "Password changed successfully"}
