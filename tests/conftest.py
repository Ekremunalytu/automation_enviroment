"""
ExTrace test fixtures.

DB-backed fixtures stay opt-in so unit and mocked router tests do not
initialize the test PostgreSQL engine unless they explicitly request it.
"""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Import application components
from appcore.storage.models import Base
from appcore.api.deps import get_db

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
        # Reset the dedicated test schema up front so interrupted smoke or DB
        # runs do not leak active-job rows into later sessions.
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except OperationalError:
        engine.dispose()
        pytest.skip(
            "Test database is unavailable. Start the postgres_test container "
            "before running requires_db tests."
        )

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


def load_test_app() -> Any:
    """Import the FastAPI app without requiring live job-storage recovery."""
    main_module = sys.modules.get("main")
    if main_module is not None:
        return main_module.app

    from workflows.marketplace import job_service

    with patch(
        "workflows.marketplace.job_service.recover_interrupted_jobs",
        return_value=0,
    ):
        main_module = importlib.import_module("main")

    main_module.recover_interrupted_jobs = job_service.recover_interrupted_jobs
    return main_module.app


@pytest.fixture(scope="function")
def mock_session() -> Session:
    """Return a lightweight SQLAlchemy session double for DB-free tests."""
    return MagicMock(spec=Session)


@pytest.fixture(scope="function")
def client(mock_session: Session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client backed by a lightweight mocked DB session."""
    app = load_test_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client backed by the real test PostgreSQL session."""
    app = load_test_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def runtime_client(test_engine: Any) -> Generator[TestClient, None, None]:
    """Create a TestClient whose request and worker sessions use the test DB."""
    app = load_test_app()
    runtime_session_factory = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )

    with (
        patch("appcore.api.deps.SessionLocal", runtime_session_factory),
        patch("appcore.db.session.SessionLocal", runtime_session_factory),
        patch(
            "workflows.marketplace.job_service.SessionLocal", runtime_session_factory
        ),
        TestClient(app) as test_client,
    ):
        yield test_client


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
