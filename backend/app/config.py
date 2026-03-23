"""Application configuration module.

This module contains all application settings loaded from environment variables.
Uses Pydantic Settings for validation and type checking.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class.

    All settings are loaded from environment variables with sensible defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Application Settings
    # ============================================
    app_name: str = Field(default="User Management System", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    secret_key: str = Field(default="", description="Application secret key")

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # CORS Settings
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string to list."""
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production", "testing"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()

    # ============================================
    # Database Settings
    # ============================================
    database_url: str = Field(
        default="postgresql+asyncpg://devuser:devpassword@localhost:5432/user_management",
        description="Database connection URL",
    )
    test_database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="Test database connection URL",
    )

    # Database Pool Settings
    db_pool_size: int = Field(default=20, description="Database pool size")
    db_max_overflow: int = Field(default=10, description="Database max overflow")
    db_pool_timeout: int = Field(default=30, description="Database pool timeout in seconds")
    db_pool_recycle: int = Field(default=1800, description="Database pool recycle time in seconds")

    # ============================================
    # Redis Settings
    # ============================================
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_password: str | None = Field(default=None, description="Redis password")

    # ============================================
    # Authentication Settings
    # ============================================
    jwt_secret_key: str = Field(
        default="",
        description="JWT secret key (min 32 characters recommended)",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days",
    )

    # Password Settings
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_max_length: int = Field(default=128, description="Maximum password length")

    # Security Settings
    account_lockout_attempts: int = Field(
        default=5,
        description="Number of failed login attempts before lockout",
    )
    account_lockout_minutes: int = Field(
        default=30,
        description="Account lockout duration in minutes",
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Number of requests allowed per window",
    )
    rate_limit_window: int = Field(
        default=3600,
        description="Rate limit window in seconds",
    )

    # ============================================
    # Logging Settings
    # ============================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level value."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return upper_v

    # ============================================
    # Email Settings (Optional)
    # ============================================
    smtp_host: str | None = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: str | None = Field(default=None, description="SMTP username")
    smtp_password: str | None = Field(default=None, description="SMTP password")
    smtp_tls: bool = Field(default=True, description="Use TLS for SMTP")
    from_email: str = Field(default="noreply@example.com", description="From email address")

    # ============================================
    # Computed Properties
    # ============================================
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    @property
    def database_url_async(self) -> str:
        """Get async database URL for current environment."""
        if self.is_testing:
            return self.test_database_url
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to avoid reloading settings on every call.
    """
    return Settings()


# Global settings instance
settings = get_settings()
