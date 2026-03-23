"""Rate limiting middleware.

This module provides rate limiting functionality using Redis
or in-memory storage as fallback.
"""

import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.exceptions import RateLimitException
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory rate limit storage (use Redis in production)
_rate_limit_store: dict[str, dict] = {}


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests: int = 100  # Number of requests allowed
    window: int = 3600   # Time window in seconds


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, requests: int = None, window: int = None):
        """Initialize rate limiter.

        Args:
            requests: Number of requests allowed in window
            window: Time window in seconds
        """
        self.requests = requests or settings.rate_limit_requests
        self.window = window or settings.rate_limit_window

    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for the client

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()
        window_start = now - self.window

        # Initialize or get existing requests
        if key not in _rate_limit_store:
            _rate_limit_store[key] = {
                "requests": [],
                "count": 0,
            }

        record = _rate_limit_store[key]

        # Clean up old requests outside the window
        record["requests"] = [
            ts for ts in record["requests"]
            if ts > window_start
        ]

        # Count requests in current window
        current_count = len(record["requests"])

        # Check if allowed
        if current_count >= self.requests:
            # Calculate retry after
            oldest_request = min(record["requests"])
            retry_after = int(oldest_request + self.window - now)

            info = {
                "allowed": False,
                "limit": self.requests,
                "remaining": 0,
                "reset_time": int(oldest_request + self.window),
                "retry_after": max(0, retry_after),
            }
            return False, info

        # Allow request and record it
        record["requests"].append(now)
        record["count"] = current_count + 1

        info = {
            "allowed": True,
            "limit": self.requests,
            "remaining": self.requests - current_count - 1,
            "reset_time": int(now + self.window),
        }
        return True, info

    def get_rate_limit_info(self, key: str) -> dict:
        """Get current rate limit status.

        Args:
            key: Unique identifier for the client

        Returns:
            Rate limit information
        """
        now = time.time()
        window_start = now - self.window

        if key not in _rate_limit_store:
            return {
                "limit": self.requests,
                "remaining": self.requests,
                "reset_time": int(now + self.window),
            }

        record = _rate_limit_store[key]

        # Clean up old requests
        record["requests"] = [
            ts for ts in record["requests"]
            if ts > window_start
        ]

        current_count = len(record["requests"])

        if current_count > 0:
            oldest_request = min(record["requests"])
            reset_time = int(oldest_request + self.window)
        else:
            reset_time = int(now + self.window)

        return {
            "limit": self.requests,
            "remaining": max(0, self.requests - current_count),
            "reset_time": reset_time,
        }


def get_client_key(request: Request, use_user: bool = True) -> str:
    """Generate a unique key for rate limiting.

    Args:
        request: FastAPI request
        use_user: Whether to include user ID in key if authenticated

    Returns:
        Rate limit key
    """
    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    # Include user ID if available
    if use_user and hasattr(request.state, "user"):
        user = request.state.user
        if user and "id" in user:
            return f"user:{user['id']}"

    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting all requests."""

    def __init__(
        self,
        app,
        default_requests: int = None,
        default_window: int = None,
        auth_requests: int = None,
        auth_window: int = None,
    ):
        """Initialize middleware.

        Args:
            app: FastAPI application
            default_requests: Default rate limit for unauthenticated users
            default_window: Default window for unauthenticated users
            auth_requests: Rate limit for authenticated users
            auth_window: Window for authenticated users
        """
        super().__init__(app)
        self.default_limiter = RateLimiter(default_requests, default_window)
        self.auth_limiter = RateLimiter(
            auth_requests or (default_requests or 100) * 10,
            auth_window or default_window or 3600,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Determine which limiter to use
        is_authenticated = self._is_authenticated(request)
        limiter = self.auth_limiter if is_authenticated else self.default_limiter

        # Get client key
        key = get_client_key(request, use_user=is_authenticated)

        # Check rate limit
        allowed, info = limiter.is_allowed(key)

        # Add rate limit headers
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(info["reset_time"])

        if not allowed:
            retry_after = info.get("retry_after", self.default_limiter.window)
            response.headers["Retry-After"] = str(retry_after)
            response.status_code = 429

            logger.warning(
                "Rate limit exceeded",
                key=key,
                path=request.url.path,
                retry_after=retry_after,
            )

        return response

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated.

        Args:
            request: FastAPI request

        Returns:
            True if authenticated
        """
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ")


def rate_limit(
    requests: int = None,
    window: int = None,
    key_func: Callable[[Request], str] = None,
):
    """Decorator for rate limiting specific endpoints.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key

    Returns:
        Decorator function

    Example:
        ```python
        @router.post("/login")
        @rate_limit(requests=5, window=300)  # 5 attempts per 5 minutes
        async def login(...):
            pass
        ```
    """
    limiter = RateLimiter(requests, window)

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Get request from args/kwargs
            request = kwargs.get("request")
            if not request and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                key = key_func(request) if key_func else get_client_key(request)
                allowed, info = limiter.is_allowed(key)

                if not allowed:
                    raise RateLimitException(retry_after=info.get("retry_after"))

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Endpoint-specific rate limits
login_rate_limit = rate_limit(requests=5, window=300)  # 5 per 5 minutes
register_rate_limit = rate_limit(requests=3, window=3600)  # 3 per hour
password_reset_rate_limit = rate_limit(requests=3, window=3600)  # 3 per hour
