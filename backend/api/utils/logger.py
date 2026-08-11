"""
Logging configuration for the API.
"""

import logging
import sys

from api.config import settings


def setup_logger(name: str = "AIHallucinationAPI") -> logging.Logger:
    """
    Configure and return a logger instance.
    """

    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


logger = setup_logger()