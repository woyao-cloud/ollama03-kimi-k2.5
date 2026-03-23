"""JWT token service module.

This module provides JWT token generation, verification, and management
using python-jose with cryptographic backend.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.schemas.auth import TokenPayload

logger = get_logger(__name__)

# Algorithm used for JWT signing
ALGORITHM = settings.jwt_algorithm


def create_token(
    subject: str | uuid.UUID,
    token_type: str = "access",
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Create a JWT token.

    Args:
        subject: Token subject (usually user ID)
        token_type: Type of token ("access" or "refresh")
        expires_delta: Token expiration time, defaults to config settings
        extra_claims: Additional claims to include in the token

    Returns:
        Tuple of (encoded_token, expiration_datetime)

    Raises:
        AuthenticationException: If token creation fails

    Example:
        >>> token, exp = create_token(
        ...     subject="user-123",
        ...     token_type="access",
        ...     extra_claims={"roles": ["user"]}
        ... )
    """
    try:
        # Convert UUID to string if needed
        if isinstance(subject, uuid.UUID):
            subject = str(subject)

        # Determine expiration time
        if token_type == "access":
            default_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        elif token_type == "refresh":
            default_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
        else:
            default_expires = timedelta(minutes=15)

        expires = expires_delta or default_expires
        expire_datetime = datetime.now(timezone.utc) + expires

        # Create JWT ID (jti) for token tracking
        jti = str(uuid.uuid4())

        # Build payload
        payload = {
            "sub": subject,
            "exp": expire_datetime,
            "iat": datetime.now(timezone.utc),
            "jti": jti,
            "type": token_type,
        }

        # Add extra claims
        if extra_claims:
            payload.update(extra_claims)

        # Encode token
        encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)
        logger.debug(
            "Token created",
            token_type=token_type,
            subject=subject,
            expires_at=expire_datetime.isoformat(),
        )
        return encoded, expire_datetime

    except Exception as e:
        logger.error("Failed to create token", error=str(e))
        raise AuthenticationException("Failed to create authentication token")


def verify_token(token: str, token_type: str | None = None) -> TokenPayload:
    """Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh"), None to skip check

    Returns:
        Decoded token payload

    Raises:
        AuthenticationException: If token is invalid or expired

    Example:
        >>> payload = verify_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...")
        >>> print(payload.sub)
        "user-123"
    """
    try:
        # Decode token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])

        # Validate token type if specified
        if token_type and payload.get("type") != token_type:
            logger.warning(
                "Token type mismatch",
                expected=token_type,
                actual=payload.get("type"),
            )
            raise AuthenticationException(f"Invalid token type, expected {token_type}")

        # Convert to TokenPayload
        token_payload = TokenPayload(
            sub=uuid.UUID(payload["sub"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload.get("jti"),
            type=payload.get("type", "access"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
        )

        logger.debug("Token verified successfully", jti=token_payload.jti)
        return token_payload

    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        raise AuthenticationException("Invalid or expired token")
    except ValueError as e:
        logger.warning("Invalid token payload", error=str(e))
        raise AuthenticationException("Invalid token format")
    except Exception as e:
        logger.error("Unexpected token verification error", error=str(e))
        raise AuthenticationException("Token verification failed")


def create_access_token(
    user_id: uuid.UUID,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> tuple[str, datetime]:
    """Create an access token for a user.

    Args:
        user_id: User ID
        roles: User roles
        permissions: User permissions

    Returns:
        Tuple of (access_token, expiration_datetime)
    """
    extra_claims = {}
    if roles:
        extra_claims["roles"] = roles
    if permissions:
        extra_claims["permissions"] = permissions

    return create_token(
        subject=user_id,
        token_type="access",
        extra_claims=extra_claims,
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """Create a refresh token for a user.

    Args:
        user_id: User ID

    Returns:
        Tuple of (refresh_token, expiration_datetime)
    """
    return create_token(
        subject=user_id,
        token_type="refresh",
    )


def create_token_pair(
    user_id: uuid.UUID,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> dict[str, Any]:
    """Create both access and refresh tokens.

    Args:
        user_id: User ID
        roles: User roles
        permissions: User permissions

    Returns:
        Dictionary with tokens and metadata
    """
    access_token, access_exp = create_access_token(user_id, roles, permissions)
    refresh_token, refresh_exp = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int((access_exp - datetime.now(timezone.utc)).total_seconds()),
        "refresh_expires_in": int((refresh_exp - datetime.now(timezone.utc)).total_seconds()),
        "access_expires_at": access_exp,
        "refresh_expires_at": refresh_exp,
    }


def get_token_jti(token: str) -> str | None:
    """Extract JWT ID (jti) from token without full verification.

    Args:
        token: JWT token

    Returns:
        JWT ID if present, None otherwise
    """
    try:
        # Decode without verification to get the payload
        payload = jwt.get_unverified_claims(token)
        return payload.get("jti")
    except JWTError:
        return None


def get_token_expiry(token: str) -> datetime | None:
    """Extract expiration time from token without full verification.

    Args:
        token: JWT token

    Returns:
        Expiration datetime if present, None otherwise
    """
    try:
        payload = jwt.get_unverified_claims(token)
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except JWTError:
        return None
