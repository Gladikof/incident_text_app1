"""
Конфігурація додатку
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Налаштування додатку"""

    # App
    APP_NAME: str = "Service Desk ML System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./servicedesk.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-please-make-it-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 години

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
