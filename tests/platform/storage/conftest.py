"""Storage-test fixtures — fresh Postgres database per test for alembic round-trip tests.

The session-scoped ``test_engine`` from ``tests/conftest.py`` is shared and mutated
only via ``Base.metadata.create_all``. Alembic round-trip tests need an isolated DB
so DDL failures cannot poison sibling tests' schema or the shared ``alembic_version``
table — closes the W13-4.5 deferral by replacing the previous ``@pytest.mark.skip``.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool


_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


def _get_test_database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL", "")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_TEST_PORT", "5434")
    db = os.getenv("POSTGRES_TEST_DB", "test_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="function")
def fresh_alembic_engine() -> Generator[tuple[Any, str], None, None]:
    """Create a throwaway Postgres database, upgrade to head via alembic, yield (engine, url).

    Each invocation creates a database named ``test_alembic_<uuid8>`` so concurrent or
    sequential tests cannot poison each other's schema even when DDL fails mid-flight.
    Tears down by terminating lingering backends and ``DROP DATABASE``.
    """
    base_url = _get_test_database_url()
    parsed = urlparse(base_url)
    fresh_db_name = f"test_alembic_{uuid.uuid4().hex[:8]}"

    maint_url = urlunparse(parsed._replace(path="/postgres"))
    try:
        maint_engine = create_engine(
            maint_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
        )
        with maint_engine.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{fresh_db_name}"'))
    except OperationalError:
        pytest.skip(
            "Test database is unavailable. Start the postgres_test container "
            "before running requires_db tests."
        )
        return

    fresh_engine: Any = None
    prior_db_url = os.environ.get("DATABASE_URL")
    try:
        fresh_url = urlunparse(parsed._replace(path=f"/{fresh_db_name}"))
        fresh_engine = create_engine(fresh_url, poolclass=NullPool)

        # alembic/env.py reads DATABASE_URL directly, so override for the
        # upgrade head call so migrations target the throwaway DB.
        os.environ["DATABASE_URL"] = fresh_url

        from alembic import command
        from alembic.config import Config

        cfg = Config(str(_ALEMBIC_INI))
        cfg.set_main_option("sqlalchemy.url", fresh_url)
        # Suppress alembic env.py's fileConfig() call — it sets
        # disable_existing_loggers=True globally and breaks pytest caplog
        # for sibling tests run later in the same session.
        cfg.config_file_name = None
        command.upgrade(cfg, "head")

        yield fresh_engine, fresh_url
    finally:
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url
        if fresh_engine is not None:
            fresh_engine.dispose()
        try:
            with maint_engine.connect() as conn:
                conn.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = :dbname AND pid <> pg_backend_pid()"
                    ),
                    {"dbname": fresh_db_name},
                )
                conn.execute(text(f'DROP DATABASE IF EXISTS "{fresh_db_name}"'))
        finally:
            maint_engine.dispose()
