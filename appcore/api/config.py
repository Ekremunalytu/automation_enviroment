"""
appcore/api/config.py
=====================

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
    from appcore.api.config import settings

    # Access config
    print(settings.project.NAME)
    print(settings.api.PORT)
    print(settings.db.url)
"""

import os

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ADR 0007 — Local Network Binding Discipline.
# Defaults bind loopback only. Operators that genuinely need LAN exposure
# set EXTRACE_ALLOW_LAN=1; the post-init hook on APISettings substitutes
# the wildcard binding when the field still holds the loopback default.
# See documents/runbooks/lan-exposure.md for the operator-side checklist.
_EXTRACE_ALLOW_LAN_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _allow_lan() -> bool:
    raw = os.getenv("EXTRACE_ALLOW_LAN", "").strip().lower()
    return raw in _EXTRACE_ALLOW_LAN_TRUTHY


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
    # Offline intake directory for air-gapped runs. Operators drop raw
    # ``.vsix`` files here (no marketplace egress); the Offline tab scans it
    # and ingests each package through the same hardened extract path as a
    # marketplace download. Lives *under* EXTENSION_DIR so the existing
    # ``./extensions`` bind mount already exposes it inside the API container
    # — no compose change required. Overridable via ``PROJECT_OFFLINE_DIR``.
    OFFLINE_DIR: str = "extensions/offline"

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

    Defaults bind loopback only per ADR 0007. EXTRACE_ALLOW_LAN=1 substitutes
    the wildcard binding for fields that still hold the loopback default;
    explicit env overrides win over the substitution.
    """

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    DEBUG: bool = False
    HEALTH_STATUS: str = "OK"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    GZIP_MINIMUM_SIZE: int = 2000
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Content-Type,Authorization"
    CORS_ALLOW_CREDENTIALS: bool = False

    def model_post_init(self, _ctx: object, /) -> None:
        if not _allow_lan():
            return
        if self.HOST == "127.0.0.1":
            self.HOST = "0.0.0.0"  # nosec B104
        if self.CORS_ALLOW_ORIGINS == "http://localhost:3000":
            self.CORS_ALLOW_ORIGINS = "*"

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
    PLAYWRIGHT_FLOW_DIR: str = "/home/executor/flows/playwright"
    ENTRYPOINT_MODULE: str = "executor.flows.playwright.entrypoint"
    RELOAD_SCRIPT_MODULE: str = "executor.flows.playwright.reload_vscode"
    RESET_SCRIPT_MODULE: str = "executor.flows.playwright.reset_state"
    DOCKER_EXEC_TIMEOUT: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EXECUTOR_",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class StaticAnalysisSettings(BaseSettings):
    """
    Static pre-check stage feature flag + run knobs (ES-3b, ADR 0016).
    Prefix: STATIC_ANALYSIS_

    ``ENABLED`` is ON by default from the ES-5 close-out, which flipped it after
    smoke evidence passed (ADR 0016 §Operational notes). It shares the
    ``STATIC_ANALYSIS_ENABLED`` env var with the executor-side
    ``executor.config.StaticAnalysisSettings`` so a single flag gates both the
    app orchestrator and the host container driver. ``RULES_VERSION`` /
    ``TIMEOUT_BUDGET_S`` are the explicit params the orchestrator threads into
    ``workflows.marketplace.static_analysis.run_static_analysis``.
    """

    ENABLED: bool = True
    RULES_VERSION: str = "0.0.0"
    TIMEOUT_BUDGET_S: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STATIC_ANALYSIS_",
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
    static_analysis: StaticAnalysisSettings = StaticAnalysisSettings()


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
