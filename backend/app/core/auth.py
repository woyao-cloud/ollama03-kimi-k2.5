"""Authentication dependencies.

This module provides FastAPI dependencies for OAuth2 authentication
and JWT token verification.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.core.exceptions import AuthenticationException
from app.core.jwt import verify_token
from app.core.logging import get_logger

logger = get_logger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT",
)


async def get_current_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """Extract and return the bearer token from request.

    Args:
        token: Bearer token from Authorization header

    Returns:
        Raw token string

    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """Validate JWT token and return user ID.

    Args:
        token: JWT access token

    Returns:
        User ID as string

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = verify_token(token, token_type="access")
        return str(payload.sub)
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Validate JWT token and return user data.

    This dependency should be used to protect routes that require
    authenticated users. It validates the token and returns user info.

    Args:
        token: JWT access token

    Returns:
        User data dictionary

    Raises:
        HTTPException: If token is invalid, expired, or user is inactive

    Example:
        ```python
        @router.get("/me")
        async def get_me(current_user: dict = Depends(get_current_user)):
            return current_user
        ```
    """
    try:
        payload = verify_token(token, token_type="access")

        # Build user data from token payload
        user_data = {
            "id": str(payload.sub),
            "roles": payload.roles,
            "permissions": payload.permissions,
        }

        logger.debug(
            "Current user authenticated",
            user_id=user_data["id"],
        )

        return user_data

    except AuthenticationException as e:
        logger.warning("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> dict | None:
    """Get user data if token is provided, otherwise return None.

    This is useful for endpoints that work both with and without authentication.

    Args:
        token: Optional JWT access token

    Returns:
        User data or None

    Example:
        ```python
        @router.get("/public-resource")
        async def get_resource(user: dict | None = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user['id']}"}
            return {"message": "Hello guest"}
        ```
    """
    if not token:
        return None

    try:
        payload = verify_token(token, token_type="access")
        return {
            "id": str(payload.sub),
            "roles": payload.roles,
            "permissions": payload.permissions,
        }
    except AuthenticationException:
        return None


# Type aliases for convenient use
current_user_dep = Annotated[dict, Depends(get_current_user)]
current_user_id_dep = Annotated[str, Depends(get_current_user_id)]
optional_user_dep = Annotated[dict | None, Depends(get_optional_user)]
