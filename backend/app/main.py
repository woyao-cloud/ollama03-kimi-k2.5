"""FastAPI application entry point.

This module initializes and configures the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.schemas.common import HealthCheckResponse

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    # Shutdown
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        User Management System API

        ## Features

        - **Authentication**: JWT-based authentication with access and refresh tokens
        - **Authorization**: Role-based access control (RBAC) with fine-grained permissions
        - **User Management**: Complete CRUD operations for user accounts
        - **Role Management**: Create and manage roles with permissions
        - **Permission System**: Resource-action based permissions
        - **Audit Logging**: Track all user actions
        - **Rate Limiting**: API rate limiting to prevent abuse
        - **Account Security**: Account lockout after failed login attempts

        ## Authentication

        This API uses OAuth2 Password Bearer tokens for authentication.
        Include the token in the Authorization header:
        ```
        Authorization: Bearer <your_token>
        ```

        ## Rate Limits

        - Unauthenticated: 100 requests per hour
        - Authenticated: 1000 requests per hour
        - Login attempts: 5 per 5 minutes

        ## Permissions

        Permissions follow the format `resource:action`, e.g.:
        - `users:read` - Read user information
        - `users:create` - Create new users
        - `roles:update` - Update roles
        """,
        terms_of_service="http://example.com/terms",
        contact={
            "name": "API Support",
            "url": "http://example.com/support",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {"name": "health", "description": "Health check endpoints"},
            {"name": "authentication", "description": "Authentication operations"},
            {"name": "users", "description": "User management operations"},
            {"name": "roles", "description": "Role management operations"},
            {"name": "permissions", "description": "Permission operations"},
        ],
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        default_requests=100,
        default_window=3600,
        auth_requests=1000,
        auth_window=3600,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create application instance
app = create_application()


@app.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.is_development else None,
    }
