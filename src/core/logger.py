"""Logging module for the sports model."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR


def setup_logger(name: str = "sports_model") -> logging.Logger:
    """Set up and configure logger.

    Args:
        name: The name of the logger.

    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    # Create file handler
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create the logs directory if it doesn't exist
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Create and configure the default logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: The name of the logger.

    Returns:
        A configured logger instance.
    """
    return setup_logger(name)
