"""
Bull Sage - Centralized Logging Module
======================================

Provides consistent logging across all modules with:
- Structured format with timestamps
- Module-level loggers
- Helper functions for common patterns
"""

import logging
import sys
from typing import Optional, Any
from functools import wraps
import traceback

# Configure root logger once
_configured = False

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the application.
    Should be called once at application startup.
    """
    global _configured
    if _configured:
        return

    # Format: timestamp - module - level - message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Usage:
        from core.logging import get_logger
        logger = get_logger(__name__)
    """
    setup_logging()  # Ensure logging is configured
    return logging.getLogger(name)


def log_error(logger: logging.Logger, operation: str, error: Exception, context: Optional[dict] = None) -> None:
    """
    Log an error with consistent formatting.

    Args:
        logger: The logger instance
        operation: What operation failed (e.g., "fetch_market_data")
        error: The exception that occurred
        context: Optional dict with additional context
    """
    ctx_str = f" | Context: {context}" if context else ""
    logger.error(f"[{operation}] {type(error).__name__}: {error}{ctx_str}")


def log_warning(logger: logging.Logger, operation: str, message: str, context: Optional[dict] = None) -> None:
    """
    Log a warning with consistent formatting.
    """
    ctx_str = f" | Context: {context}" if context else ""
    logger.warning(f"[{operation}] {message}{ctx_str}")


def log_api_call(logger: logging.Logger, api_name: str, endpoint: str, success: bool,
                 response_time_ms: Optional[float] = None, error: Optional[str] = None) -> None:
    """
    Log an API call result.
    """
    status = "OK" if success else "FAILED"
    time_str = f" ({response_time_ms:.0f}ms)" if response_time_ms else ""
    error_str = f" - {error}" if error else ""
    logger.info(f"[API:{api_name}] {endpoint} -> {status}{time_str}{error_str}")


def log_exception(logger: logging.Logger, operation: str, include_traceback: bool = False) -> None:
    """
    Log the current exception with optional traceback.
    Call this inside an except block.
    """
    if include_traceback:
        logger.exception(f"[{operation}] Exception occurred")
    else:
        import sys
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type and exc_value:
            logger.error(f"[{operation}] {exc_type.__name__}: {exc_value}")


def with_logging(operation: str, reraise: bool = True):
    """
    Decorator to automatically log exceptions in a function.

    Usage:
        @with_logging("fetch_prices")
        async def fetch_prices():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log_error(logger, operation, e)
                if reraise:
                    raise
                return None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(logger, operation, e)
                if reraise:
                    raise
                return None

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Initialize logging on module import
setup_logging()
