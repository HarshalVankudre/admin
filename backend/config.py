"""
Configuration settings for the Admin Dashboard API.

Centralizes all environment variables and configuration options.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL database configuration."""
    
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "ruko_admin"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    connect_timeout: int = field(default_factory=lambda: int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5")))
    app_name: str = field(default_factory=lambda: os.getenv("POSTGRES_APP_NAME", "ruko-admin-dashboard"))
    pool_min: int = field(default_factory=lambda: int(os.getenv("DB_POOL_MIN", "1")))
    pool_max: int = field(default_factory=lambda: int(os.getenv("DB_POOL_MAX", "10")))

    def to_connect_kwargs(self) -> dict:
        """Return kwargs for psycopg2.connect()."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
            "application_name": self.app_name,
        }


@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""
    
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "0") == "1")
    init_db_on_startup: bool = field(default_factory=lambda: os.getenv("ADMIN_DB_INIT_ON_STARTUP", "0") == "1")


@dataclass(frozen=True)
class Settings:
    """Combined application settings."""
    
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    app: AppConfig = field(default_factory=AppConfig)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
