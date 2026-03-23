"""Global error handling module.

This module provides custom exceptions and exception handlers for the FastAPI application.
"""

from typing import Any, Dict, Type

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception.

    Attributes:
        status_code: HTTP status code
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error details
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, resource_id: str | None = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="not_found",
            message=message,
            details={"resource": resource, "id": resource_id},
        )


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str, field: str | None = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="validation_error",
            message=message,
            details=details,
        )


class AuthenticationException(AppException):
    """Authentication failed exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="authentication_error",
            message=message,
        )


class AuthorizationException(AppException):
    """Authorization failed exception."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="authorization_error",
            message=message,
        )


class ConflictException(AppException):
    """Resource conflict exception."""

    def __init__(self, message: str, field: str | None = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="conflict_error",
            message=message,
            details=details,
        )


class RateLimitException(AppException):
    """Rate limit exceeded exception."""

    def __init__(self, retry_after: int | None = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="rate_limit_exceeded",
            message="Too many requests, please try again later",
            details=details,
        )


def create_error_response(exc: AppException) -> Dict[str, Any]:
    """Create error response dictionary from AppException.

    Args:
        exc: Application exception

    Returns:
        Error response dictionary
    """
    response: Dict[str, Any] = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
        }
    }
    if exc.details:
        response["error"]["details"] = exc.details
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException instances."""
    logger.warning(
        "Application exception",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle RequestValidationError."""
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        errors.append(error_detail)

    logger.warning(
        "Validation error",
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": {"errors": errors},
            }
        },
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic ValidationError."""
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        errors.append(error_detail)

    logger.warning(
        "Pydantic validation error",
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Data validation failed",
                "details": {"errors": errors},
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger.exception(
        "Unhandled exception",
        exception_type=type(exc).__name__,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An internal server error occurred",
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
