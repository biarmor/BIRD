"""
BIRD Backend Configuration Settings

Centralized configuration management using Pydantic Settings.
Supports environment variables and .env file loading.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application Settings with environment variable support."""

    # Application
    app_name: str = "BIRD"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./data/bird.db"
    database_echo: bool = False

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_small: str = "qwen2.5:7b"
    ollama_model_medium: str = "qwen3:8b"
    ollama_model_large: str = "qwen3:14b"
    ollama_timeout: int = 300

    # ChromaDB Configuration
    chromadb_path: str = "./data/chromadb"
    chromadb_collection_name: str = "bird_intelligence"

    # Session Configuration
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    session_expire_seconds: int = 86400

    # API Configuration
    api_v1_str: str = "/api/v1"
    api_v2_str: str = "/api/v2"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Optional: Frontier Model Integration (Phase 5)
    claude_api_key: Optional[str] = None
    fable_api_key: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create project directories if they don't exist
def ensure_directories():
    """Ensure all required directories exist."""
    settings = get_settings()
    
    # Create data directory
    Path("./data").mkdir(exist_ok=True)
    
    # Create ChromaDB directory
    Path(settings.chromadb_path).mkdir(exist_ok=True)
    
    # Create logs directory
    Path("./logs").mkdir(exist_ok=True)


if __name__ == "__main__":
    settings = get_settings()
    print(f"BIRD Backend Configuration")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Database: {settings.database_url}")
    print(f"Ollama: {settings.ollama_base_url}")
