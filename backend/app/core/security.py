"""Security utilities module.

This module provides security-related functions including password hashing
using Argon2id (recommended by OWASP).
"""

from passlib.context import CryptContext

from app.core.logging import get_logger

logger = get_logger(__name__)

# Configure password hashing with Argon2id
# Argon2id is the winner of the Password Hashing Competition
# and is recommended by OWASP for password storage
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # Argon2id specific parameters
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=4,      # 4 parallel threads
    argon2__type="ID",          # Argon2id variant
)


def hash_password(password: str) -> str:
    """Hash a plain text password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Example:
        >>> hashed = hash_password("my_password")
        >>> print(hashed)
        '$argon2id$v=19$m=65536,t=3,p=4$...'
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error("Failed to hash password", error=str(e))
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug("Password verification completed", is_valid=is_valid)
        return is_valid
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def generate_password_reset_token() -> str:
    """Generate a secure random token for password reset.

    Returns:
        Secure random token string

    Note:
        This token should be stored in the database with an expiration time
        and sent to the user via email.
    """
    import secrets
    import string

    # Generate a 32-byte token (256 bits of entropy)
    alphabet = string.ascii_letters + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(32))
    return token


def generate_email_verification_token() -> str:
    """Generate a secure random token for email verification.

    Returns:
        Secure random token string
    """
    import secrets
    import string

    # Generate a 32-byte token
    alphabet = string.ascii_letters + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(32))
    return token
