"""
Configuration settings for the backend.
"""

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


class Settings:
    """Application settings."""

    APP_NAME = os.getenv(
        "APP_NAME",
        "AI Hallucination Mitigation API"
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "1.0.0"
    )

    HOST = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    PORT = int(
        os.getenv("PORT", 8000)
    )

    DEBUG = os.getenv(
        "DEBUG",
        "True"
    ).lower() == "true"

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    TOP_K = int(
        os.getenv("TOP_K", 5)
    )

    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2"
    )


settings = Settings()