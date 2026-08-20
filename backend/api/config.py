"""
Configuration settings for the backend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load this project's backend/.env regardless of the launch directory.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


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
        "0.0.0.0"
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

    RETRIEVAL_MIN_SIMILARITY = float(os.getenv("RETRIEVAL_MIN_SIMILARITY", "0.35"))

    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    LLM_MODEL = os.getenv("LLM_MODEL", "")

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    SCIFACT_CORPUS_PATH = Path(os.getenv("SCIFACT_CORPUS_PATH", PROJECT_ROOT / "data" / "scifact" / "corpus.jsonl"))
    SCIFACT_MODEL_PATH = Path(os.getenv("SCIFACT_MODEL_PATH", PROJECT_ROOT / "models" / "scifact"))
    ANSWER_CORPUS_PATH = os.getenv("ANSWER_CORPUS_PATH", "")
    KNOWLEDGE_PROVIDER = os.getenv("KNOWLEDGE_PROVIDER", "wikipedia").strip().lower()
    KNOWLEDGE_API_URL = os.getenv("KNOWLEDGE_API_URL", "https://en.wikipedia.org/w/api.php")
    KNOWLEDGE_TIMEOUT_SECONDS = float(os.getenv("KNOWLEDGE_TIMEOUT_SECONDS", "8"))
    KNOWLEDGE_TOP_K = int(os.getenv("KNOWLEDGE_TOP_K", "8"))
    KNOWLEDGE_MIN_SIMILARITY = float(os.getenv("KNOWLEDGE_MIN_SIMILARITY", "0.45"))
    SCIFACT_MIN_SIMILARITY = float(os.getenv("SCIFACT_MIN_SIMILARITY", "0.50"))
    SCIFACT_VERIFY_GENERAL = os.getenv("SCIFACT_VERIFY_GENERAL", "false").lower() == "true"

    # MongoDB Atlas Configuration
    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        os.getenv("MONGO_URI", "")
    ).strip()
    MONGODB_DB_NAME = os.getenv(
        "MONGODB_DB_NAME",
        os.getenv("MONGO_DB", "ai_hallucination_mitigation")
    ).strip()
    MONGODB_TIMEOUT_MS = int(os.getenv("MONGODB_TIMEOUT_MS", "4000"))

    # JWT Authentication Configuration
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "super-secret-key-change-in-production-ai-hallucination-mitigation-2026"
    )
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://192.168.137.130:8080,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
