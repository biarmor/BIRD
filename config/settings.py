"""
BIRD Backend Configuration Settings

Simple configuration management using environment variables.
"""

import os
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application Settings with environment variable support."""

    # Application
    app_name: str = os.getenv("APP_NAME", "BIRD")
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bird.db")
    database_echo: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"

    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model_small: str = os.getenv("OLLAMA_MODEL_SMALL", "qwen2.5:7b")
    ollama_model_medium: str = os.getenv("OLLAMA_MODEL_MEDIUM", "qwen3:8b")
    ollama_model_large: str = os.getenv("OLLAMA_MODEL_LARGE", "qwen3:14b")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))

    # ChromaDB Configuration
    chromadb_path: str = os.getenv("CHROMADB_PATH", "./data/chromadb")

    # Session Configuration
    session_expire_seconds: int = int(os.getenv("SESSION_EXPIRE_SECONDS", "86400"))

    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
    api_v2_str: str = os.getenv("API_V2_STR", "/api/v2")

    # CORS Origins
    cors_origins: List[str] = []
    _cors_origins_raw = os.getenv("CORS_ORIGINS")
    if _cors_origins_raw:
        try:
            cors_origins = json.loads(_cors_origins_raw)
        except Exception:
            cors_origins = ["http://localhost:3000", "http://localhost:8000"]
    else:
        cors_origins = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

