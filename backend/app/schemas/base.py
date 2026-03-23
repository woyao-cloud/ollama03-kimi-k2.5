"""Base Pydantic schemas.

This module provides base schema classes used across the application.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class BaseResponse(BaseSchema):
    """Base response schema.

    All API responses should inherit from this class.
    """

    pass


class BaseCreateSchema(BaseSchema):
    """Base schema for create operations."""

    pass


class BaseUpdateSchema(BaseSchema):
    """Base schema for update operations.

    All fields are optional to allow partial updates.
    """

    pass


class BaseInDBSchema(BaseSchema):
    """Base schema for database models.

    Includes common fields like id, created_at, updated_at.
    """

    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


T = TypeVar("T")


class PaginationMeta(BaseSchema):
    """Pagination metadata schema."""

    page: int = Field(..., description="Current page number", ge=1)
    per_page: int = Field(..., description="Items per page", ge=1, le=100)
    total: int = Field(..., description="Total number of items", ge=0)
    total_pages: int = Field(..., description="Total number of pages", ge=0)
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper.

    Generic response that can be used for any paginated resource.
    """

    data: list[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseSchema):
    """Error detail schema."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: str | None = Field(None, description="Error type")


class ErrorResponse(BaseSchema):
    """Error response schema.

    Standard error response format for all API errors.
    """

    error: dict[str, Any] = Field(..., description="Error details")


class SuccessResponse(BaseSchema):
    """Success response schema.

    Simple success message response.
    """

    message: str = Field(..., description="Success message")
    data: Any | None = Field(None, description="Optional response data")
