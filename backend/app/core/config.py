"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Look for .env in backend/ dir regardless of where uvicorn is launched from
_HERE = Path(__file__).resolve().parent.parent.parent  # backend/
_ENV_FILE = _HERE / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/timelyna"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT RS256 keys (PEM-encoded, newlines as \n in env)
    AUTH_PRIVATE_KEY: str = ""
    AUTH_PUBLIC_KEY: str = ""

    # Token expiry
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Rate limiting
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    LOGIN_WINDOW_MINUTES: int = 10

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@timelyna.com"
    FRONTEND_URL: str = "http://localhost:5173"

    # License
    LICENSE_PUBLIC_KEY: str = ""  # RS256 public key for license JWT validation
    FINANCE_LICENSE_SECRET: str = ""  # HMAC-SHA256 secret for Finance Pro license validation

    # Supabase (optionnel — pour le client JS frontend)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    
    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost,http://localhost:80,http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Singleton instance for easy import
settings = get_settings()
