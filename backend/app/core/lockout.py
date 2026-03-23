"""Account lockout mechanism.

This module provides account lockout functionality to prevent
brute force attacks.
"""

import uuid
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory store for failed attempts (should be Redis in production)
_failed_attempts: dict[str, dict] = {}
_locked_accounts: dict[str, datetime] = {}


class AccountLockoutService:
    """Service for managing account lockouts."""

    def __init__(self):
        """Initialize the lockout service."""
        self.max_attempts = settings.account_lockout_attempts
        self.lockout_duration = timedelta(minutes=settings.account_lockout_minutes)

    def record_failed_attempt(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> dict:
        """Record a failed login attempt.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            Attempt record with attempt count and lockout status
        """
        key = self._get_key(identifier, ip_address)
        now = datetime.now(timezone.utc)

        if key not in _failed_attempts:
            _failed_attempts[key] = {
                "count": 0,
                "first_attempt": now,
                "last_attempt": now,
            }

        record = _failed_attempts[key]
        record["count"] += 1
        record["last_attempt"] = now

        # Check if account should be locked
        locked = self.is_locked(identifier, ip_address)

        logger.warning(
            "Failed login attempt recorded",
            identifier=identifier,
            ip_address=ip_address,
            attempt_count=record["count"],
            is_locked=locked,
        )

        return {
            "count": record["count"],
            "is_locked": locked,
            "locked_until": self._locked_accounts.get(key),
        }

    def record_successful_login(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> None:
        """Record a successful login, clearing failed attempts.

        Args:
            identifier: Username or email
            ip_address: Optional IP address
        """
        key = self._get_key(identifier, ip_address)

        # Clear failed attempts
        if key in _failed_attempts:
            del _failed_attempts[key]

        # Clear lockout if exists
        if key in _locked_accounts:
            del _locked_accounts[key]

        logger.debug(
            "Successful login recorded - cleared failed attempts",
            identifier=identifier,
            ip_address=ip_address,
        )

    def is_locked(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> bool:
        """Check if account is locked.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            True if account is locked
        """
        key = self._get_key(identifier, ip_address)

        # Check if explicitly locked
        if key in _locked_accounts:
            locked_until = _locked_accounts[key]
            if datetime.now(timezone.utc) < locked_until:
                return True
            else:
                # Lockout expired, clear it
                del _locked_accounts[key]
                if key in _failed_attempts:
                    del _failed_attempts[key]
                return False

        # Check if should be locked based on failed attempts
        if key in _failed_attempts:
            record = _failed_attempts[key]
            if record["count"] >= self.max_attempts:
                # Lock the account
                locked_until = datetime.now(timezone.utc) + self.lockout_duration
                _locked_accounts[key] = locked_until

                logger.warning(
                    "Account locked due to too many failed attempts",
                    identifier=identifier,
                    ip_address=ip_address,
                    locked_until=locked_until.isoformat(),
                )
                return True

        return False

    def get_lockout_info(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> dict | None:
        """Get lockout information for an account.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            Lockout info or None if not locked
        """
        key = self._get_key(identifier, ip_address)

        if key not in _locked_accounts:
            return None

        locked_until = _locked_accounts[key]
        remaining = locked_until - datetime.now(timezone.utc)

        return {
            "is_locked": True,
            "locked_until": locked_until.isoformat(),
            "remaining_seconds": max(0, int(remaining.total_seconds())),
            "remaining_minutes": max(0, int(remaining.total_seconds() // 60)),
        }

    def unlock_account(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> bool:
        """Manually unlock an account.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            True if account was unlocked
        """
        key = self._get_key(identifier, ip_address)
        was_locked = key in _locked_accounts or key in _failed_attempts

        if key in _locked_accounts:
            del _locked_accounts[key]
        if key in _failed_attempts:
            del _failed_attempts[key]

        if was_locked:
            logger.info(
                "Account manually unlocked",
                identifier=identifier,
                ip_address=ip_address,
            )

        return was_locked

    def get_remaining_attempts(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> int:
        """Get number of remaining attempts before lockout.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            Number of remaining attempts
        """
        key = self._get_key(identifier, ip_address)

        if key not in _failed_attempts:
            return self.max_attempts

        remaining = self.max_attempts - _failed_attempts[key]["count"]
        return max(0, remaining)

    def _get_key(self, identifier: str, ip_address: str | None = None) -> str:
        """Generate a key for storing attempts.

        Args:
            identifier: Username or email
            ip_address: Optional IP address

        Returns:
            Storage key
        """
        if ip_address:
            return f"{identifier.lower()}:{ip_address}"
        return identifier.lower()

    def cleanup_expired(self) -> int:
        """Clean up expired lockouts and old attempts.

        Returns:
            Number of entries cleaned up
        """
        now = datetime.now(timezone.utc)
        cleaned = 0

        # Clean up expired lockouts
        expired_lockouts = [
            key for key, locked_until in _locked_accounts.items()
            if now > locked_until
        ]
        for key in expired_lockouts:
            del _locked_accounts[key]
            if key in _failed_attempts:
                del _failed_attempts[key]
            cleaned += 1

        # Clean up old failed attempts (older than lockout duration)
        cutoff = now - self.lockout_duration
        expired_attempts = [
            key for key, record in _failed_attempts.items()
            if key not in _locked_accounts and record["last_attempt"] < cutoff
        ]
        for key in expired_attempts:
            del _failed_attempts[key]
            cleaned += 1

        logger.debug("Lockout cleanup completed", cleaned=cleaned)
        return cleaned


# Global lockout service instance
lockout_service = AccountLockoutService()
