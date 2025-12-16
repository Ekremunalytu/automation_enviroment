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
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Import application components
from core.deps import get_db
from main import app
from models.models import Base

# =============================================================================
# DATABASE FIXTURES
# =============================================================================


def get_test_database_url() -> str:
    """
    Get database URL for testing.

    Priority:
    1. DATABASE_URL environment variable (CI/integration tests)
    2. Falls back to default PostgreSQL test database
    """
    return os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"
    )


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

    # Create all tables
    Base.metadata.create_all(bind=engine)

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

    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    # Rollback and cleanup
    session.close()
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
    try:
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
