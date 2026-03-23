"""Logging configuration module.

This module provides structured logging configuration using structlog.
"""

import logging
import sys
from typing import Any

import structlog

from app.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application.

    Sets up both standard library logging and structlog for consistent
    structured logging across the application.
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    shared_processors: list[Any] = [
        # Add log level to the event dict
        structlog.stdlib.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Filter by log level
        structlog.stdlib.filter_by_level,
    ]

    if settings.log_format == "json":
        # JSON format for production
        processors = [
            *shared_processors,
            # Format exceptions
            structlog.processors.format_exc_info,
            # Convert to JSON
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = [
            *shared_processors,
            # Format exceptions
            structlog.processors.format_exc_info,
            # Pretty print for console
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, defaults to calling module name

    Returns:
        BoundLogger: Configured structlog logger
    """
    return structlog.get_logger(name)
