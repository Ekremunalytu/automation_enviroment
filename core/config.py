"""
core/config.py
==============

Application Configuration Management
-------------------------------------

This module handles all application configuration using Pydantic Settings.
It provides type-safe, validated configuration loaded from environment
variables and .env files.

Structure:
    - ProjectSettings: General application metadata (name, version, env)
    - APISettings: API-specific config (host, port, workers)
    - DatabaseSettings: Database connection details
    - Settings: Main entry point combining all above

Usage:
    from core.config import settings

    # Access config
    print(settings.project.NAME)
    print(settings.api.PORT)
    print(settings.db.url)
"""

import os

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """
    General project configuration.
    """

    NAME: str = "ExTrace API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "VS Code Extension Dynamic Analysis & Automation Platform"
    ENV: str = "dev"
    EXTENSION_DIR: str = "extensions"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PROJECT_",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class APISettings(BaseSettings):
    """
    API server configuration.
    Prefix: API_
    """

    HOST: str = "0.0.0.0"  # nosec B104 (Explicitly binding to all interfaces for Docker)
    PORT: int = 8000
    WORKERS: int = 1
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="API_", env_file_encoding="utf-8", extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """
    Database connection configuration.
    Prefix: POSTGRES_

    Priority:
    1. DATABASE_URL environment variable (for Docker/CI)
    2. Constructed URL from POSTGRES_* variables (for local dev)
    """

    USER: str = "postgres"
    PASSWORD: str = "postgres"
    HOST: str = "localhost"
    PORT: int = 5432
    DB: str = "extrace"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """
        Returns database URL.
        Priority: DATABASE_URL env var > constructed from components.
        """
        # Check for DATABASE_URL first (Docker/CI override)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.USER,
                password=self.PASSWORD,
                host=self.HOST,
                port=self.PORT,
                path=self.DB,
            )
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRES_",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """
    Main entry point for application settings.
    Composes strictly separated config sections.
    """

    project: ProjectSettings = ProjectSettings()
    api: APISettings = APISettings()
    db: DatabaseSettings = DatabaseSettings()


# =============================================================================
# Global Settings Instance
# =============================================================================

settings = Settings()
"""
Singleton settings instance.
Usage:
    settings.project.NAME
    settings.api.PORT
    settings.db.URL
"""
