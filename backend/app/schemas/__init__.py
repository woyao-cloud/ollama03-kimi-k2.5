"""Schemas package initialization.

This package contains all Pydantic schemas for request/response validation.
"""

from app.schemas.auth import (
    AuthResponse,
    EmailVerificationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenPayload,
    TokenRefreshRequest,
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.base import (
    BaseCreateSchema,
    BaseInDBSchema,
    BaseResponse,
    BaseSchema,
    BaseUpdateSchema,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
)
from app.schemas.common import (
    APIInfoResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    DateRangeParams,
    FilterParams,
    HealthCheckResponse,
    PaginationParams,
    SortOrder,
    SortParams,
    StatusResponse,
    UserFilterParams,
)
from app.schemas.permission import (
    PermissionBase,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCreate,
    PermissionInDB,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdate,
)
from app.schemas.role import (
    RoleAssignRequest,
    RoleBase,
    RoleCreate,
    RoleInDB,
    RoleListResponse,
    RoleResponse,
    RoleUpdate,
)
from app.schemas.user import (
    UserCreate,
    UserInDB,
    UserListResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "BaseResponse",
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseInDBSchema",
    "PaginatedResponse",
    "PaginationMeta",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    # Common schemas
    "PaginationParams",
    "SortParams",
    "SortOrder",
    "FilterParams",
    "UserFilterParams",
    "DateRangeParams",
    "BulkDeleteRequest",
    "BulkDeleteResponse",
    "StatusResponse",
    "HealthCheckResponse",
    "APIInfoResponse",
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserListResponse",
    "UserPasswordUpdate",
    # Auth schemas
    "LoginRequest",
    "TokenPayload",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenVerifyRequest",
    "TokenVerifyResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "EmailVerificationRequest",
    "AuthResponse",
    "LogoutRequest",
    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleInDB",
    "RoleListResponse",
    "RoleAssignRequest",
    # Permission schemas
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionInDB",
    "PermissionListResponse"PermissionCheckRequest"PermissionCheckResponse"]
