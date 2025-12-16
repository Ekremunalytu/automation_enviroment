"""
ExTrace Test Configuration
==========================

Pytest fixtures and configuration for ExTrace tests.
"""

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import application components
from core.deps import get_db
from main import app
from models.models import Base

# =============================================================================
# DATABASE FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def test_engine() -> Any:
    """
    Create a test database engine.

    Uses SQLite in-memory for unit tests, or PostgreSQL if DATABASE_URL is set.
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Use PostgreSQL for integration tests
        engine = create_engine(database_url)
    else:
        # Use SQLite in-memory for unit tests
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
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
