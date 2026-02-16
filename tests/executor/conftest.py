from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def check_database_connection() -> None:
    """Override global DB gate for DB-independent executor unit tests."""
    return None
