"""
core/config.py
==============

Application Configuration Management
-------------------------------------

This module handles all application configuration using Pydantic Settings.
It provides type-safe, validated configuration loaded from environment
variables and .env files.

Why Pydantic Settings?
    1. Type Safety: Validates configuration types at startup
    2. Environment Variables: Automatic parsing from env vars
    3. .env Support: Loads from .env files for local development
    4. IDE Support: Full autocomplete and type checking
    5. Validation: Fails fast if required config is missing

Configuration Sources (Priority Order):
    1. Environment variables (highest priority)
    2. .env file in project root
    3. Default values in Settings class (lowest priority)

Usage:
    from core.config import settings

    print(settings.PROJECT_NAME)
    print(settings.DATABASE_URL)

Security Note:
    Never commit .env files with real credentials to version control.
    Use .env.example as a template for required variables.
"""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration parameters for the ExTrace API.
    Values are automatically loaded from environment variables or .env file.

    Required Environment Variables:
        DATABASE_URL: PostgreSQL connection string

    Optional Environment Variables:
        PROJECT_NAME: Override default project name
        ENV: Environment identifier (dev/staging/prod)
        EXTENSION_DIR: Path to extensions directory

    Attributes:
        PROJECT_NAME: Display name for API documentation
        ENV: Current environment (dev, staging, prod)
        DATABASE_URL: PostgreSQL DSN (Data Source Name)
        EXTENSION_DIR: Directory containing VS Code extensions

    Example .env file:
        DATABASE_URL=postgresql://user:pass@localhost:5432/extrace
        PROJECT_NAME=ExTrace API
        ENV=dev
        EXTENSION_DIR=extensions

    Validation:
        - DATABASE_URL is validated as a proper PostgreSQL DSN
        - Missing required fields raise ValidationError at startup
    """

    # =========================================================================
    # Application Identity
    # =========================================================================

    PROJECT_NAME: str = "ExTrace API"
    """
    Human-readable project name.
    Displayed in Swagger UI title and API responses.
    Default: "ExTrace API"
    """

    ENV: str = "dev"
    """
    Current environment identifier.
    Common values: "dev", "staging", "prod"
    Used for conditional behavior (logging level, debug mode, etc.)
    Default: "dev"
    """

    # =========================================================================
    # Database Configuration
    # =========================================================================

    DATABASE_URL: PostgresDsn
    """
    PostgreSQL connection string (required).
    Format: postgresql://user:password@host:port/database

    Examples:
        postgresql://postgres:password@localhost:5432/extrace
        postgresql://user:pass@db.example.com:5432/mydb

    Note: This field has no default and must be provided via
    environment variable or .env file. The application will
    fail to start if this is not configured.

    For Docker Compose:
        Set to: postgresql://postgres:password@postgres:5432/extrace
        where 'postgres' is the Docker service name.
    """

    # =========================================================================
    # Filesystem Configuration
    # =========================================================================

    EXTENSION_DIR: str = "extensions"
    """
    Path to the directory containing VS Code extensions.

    Can be relative (to project root) or absolute path.
    Extensions should be unpacked in subdirectories of this path.

    Expected structure:
        {EXTENSION_DIR}/
        ├── publisher1.ext1-1.0.0/
        │   └── package.json
        └── publisher2.ext2-2.0.0/
            └── package.json

    Default: "extensions" (relative to project root)
    """

    # =========================================================================
    # Pydantic Settings Configuration
    # =========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file in project root
        case_sensitive=True,  # Environment variables are case-sensitive
        extra="ignore",  # Ignore unknown environment variables
    )
    """
    Pydantic v2 Settings configuration.

    - env_file: Path to .env file for local development
    - case_sensitive: ENV and env are treated as different variables
    - extra: Unknown fields in .env are silently ignored
    """


# =============================================================================
# Global Settings Instance
# =============================================================================

settings = Settings()  # type: ignore[call-arg]
"""
Singleton settings instance for application-wide use.

This is instantiated at module load time, which means:
1. Configuration is validated immediately on application startup
2. Missing required fields cause immediate failure (fail-fast)
3. All modules import the same validated settings instance

Usage:
    from core.config import settings

    # Access configuration values
    db_url = settings.DATABASE_URL
    project = settings.PROJECT_NAME
"""
