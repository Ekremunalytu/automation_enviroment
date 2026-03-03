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
    STATUS: str = "Active"
    EXTENSION_DIR: str = "extensions"
    OUTPUT_DIR: str = "output"

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
    HEALTH_STATUS: str = "OK"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    GZIP_MINIMUM_SIZE: int = 2000
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        """Split comma-separated config values into trimmed list items."""
        raw_values = [item.strip() for item in value.split(",")]
        parsed_values = [item for item in raw_values if item]
        return parsed_values

    @property
    def cors_allow_origins(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_ORIGINS)

    @property
    def cors_allow_methods(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_METHODS)

    @property
    def cors_allow_headers(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_HEADERS)

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
    ECHO: bool = False
    POOL_SIZE: int = 20
    POOL_MAX_OVERFLOW: int = 40
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 3600
    POOL_PRE_PING: bool = True

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


class ExecutorSettings(BaseSettings):
    """
    Executor container configuration.
    Prefix: EXECUTOR_
    """

    CONTAINER_NAME: str = "automation_executor"
    EXTENSIONS_CONTAINER_PATH: str = "/extensions-input"
    ENTRYPOINT_PATH: str = "/home/executor/playwright/entrypoint.py"
    DOCKER_EXEC_TIMEOUT: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EXECUTOR_",
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
    executor: ExecutorSettings = ExecutorSettings()


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
