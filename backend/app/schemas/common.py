"""Common Pydantic schemas.

This module defines common schemas used across the application.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SortOrder(str, Enum):
    """Sort order enum."""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Pagination parameters schema.

    Used as query parameters for paginated endpoints.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(
        default=1,
        description="Page number (1-indexed)",
        ge=1,
    )
    per_page: int = Field(
        default=20,
        description="Number of items per page",
        ge=1,
        le=100,
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.per_page


class SortParams(BaseModel):
    """Sorting parameters schema.

    Used as query parameters for sortable endpoints.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    sort_by: str | None = Field(
        default=None,
        description="Field to sort by",
        examples=["created_at", "username", "email"],
    )
    sort_order: SortOrder = Field(
        default=SortOrder.ASC,
        description="Sort order (asc or desc)",
    )


class FilterParams(BaseModel):
    """Filter parameters schema.

    Base class for filter parameters.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    search: str | None = Field(
        default=None,
        description="Search term for text search",
    )


class UserFilterParams(FilterParams):
    """User filter parameters schema."""

    is_active: bool | None = Field(
        default=None,
        description="Filter by active status",
    )
    is_verified: bool | None = Field(
        default=None,
        description="Filter by verified status",
    )


class DateRangeParams(BaseModel):
    """Date range parameters schema.

    Used for filtering by date range.
    """

    created_from: str | None = Field(
        default=None,
        description="Filter by created date (from) - ISO 8601 format",
        examples=["2024-01-01T00:00:00Z"],
    )
    created_to: str | None = Field(
        default=None,
        description="Filter by created date (to) - ISO 8601 format",
        examples=["2024-12-31T23:59:59Z"],
    )


class BulkDeleteRequest(BaseModel):
    """Bulk delete request schema."""

    ids: list[str] = Field(
        ...,
        description="List of IDs to delete",
        min_length=1,
    )


class BulkDeleteResponse(BaseModel):
    """Bulk delete response schema."""

    deleted_count: int = Field(..., description="Number of items deleted")
    not_found_ids: list[str] = Field(
        default_factory=list,
        description="IDs that were not found",
    )


class StatusResponse(BaseModel):
    """Status response schema."""

    status: Literal["success", "error", "pending"] = Field(..., description="Status")
    message: str | None = Field(None, description="Status message")


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    timestamp: str | None = Field(None, description="Health check timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "development",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        }


class APIInfoResponse(BaseModel):
    """API information response schema."""

    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    documentation: str | None = Field(None, description="API documentation URL")
    endpoints: dict[str, str] = Field(
        default_factory=dict,
        description="Available API endpoints",
    )
