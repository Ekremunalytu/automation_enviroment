"""
ExTrace Test Configuration
==========================

Pytest fixtures and configuration for ExTrace tests.

This module uses PostgreSQL for CI integration tests to properly support
PostgreSQL-specific features (JSONB, ARRAY) used in our models.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Import application components
from appcore.api.deps import get_db
from main import app
from appcore.storage.models import Base

# =============================================================================
# DATABASE FIXTURES
# =============================================================================


def get_test_database_url() -> str:
    """
    Get database URL for testing.

    Priority:
    1. DATABASE_URL environment variable (CI/integration tests)
    2. Falls back to default PostgreSQL test database

    Note:
        Fallback uses POSTGRES_TEST_PORT (default: 5434) from docker-compose.yml
        For local development, run: docker-compose up -d postgres_test
    """
    # Build URL from individual env vars if DATABASE_URL not set
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL", "")

    # Fallback: construct from test database settings
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_TEST_PORT", "5434")
    db = os.getenv("POSTGRES_TEST_DB", "test_db")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def test_engine() -> Any:
    """
    Create a test database engine.

    Uses PostgreSQL for all tests to support JSONB and ARRAY types.
    """
    database_url = get_test_database_url()

    engine = create_engine(
        database_url,
        poolclass=NullPool,  # Use NullPool for test isolation
        echo=False,
    )

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        engine.dispose()
        raise pytest.UsageError(
            "Test database is unavailable. Start the postgres_test container "
            "before running pytest."
        ) from exc

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine: Any) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.

    Rolls back all changes after each test to ensure test isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection, future=True)
    session = session_factory()

    yield session

    # Rollback and cleanup
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# =============================================================================
# API CLIENT FIXTURES
# =============================================================================


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with database session override.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


# =============================================================================
# UTILITY FIXTURES
# =============================================================================


@pytest.fixture
def sample_extension_data() -> dict[str, Any]:
    """
    Sample extension data for testing.
    """
    return {
        "name": "test-extension",
        "version": "1.0.0",
        "publisher": "test-publisher",
        "engines": {"vscode": "^1.80.0"},
        "displayName": "Test Extension",
        "description": "A test extension for unit testing",
        "categories": ["Testing"],
        "keywords": ["test", "sample"],
        "dependencies": {"vscode-languageclient": "^8.0.0"},
        "devDependencies": {"@types/vscode": "^1.80.0", "typescript": "^5.0.0"},
        "extensionPack": ["ms-python.python", "ms-python.vscode-pylance"],
        "extensionDependencies": ["ms-vscode.cpptools"],
        "extensionKind": ["workspace"],
    }


# =============================================================================
# SKIP MARKERS FOR TESTS WITHOUT DATABASE
# =============================================================================


def pytest_configure(config: Any) -> None:
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database connection"
    )


@pytest.fixture(scope="session", autouse=True)
def check_database_connection(test_engine: Any) -> None:
    """
    Check if database is available before running tests.
    Skip all tests if database is not available.
    """
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
