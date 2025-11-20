"""Utility functions for the AI assistant."""

from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def log_error(message: str, exc_info: Optional[Exception] = None) -> None:
    """Log an error message."""
    logger.error(message, exc_info=exc_info)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)