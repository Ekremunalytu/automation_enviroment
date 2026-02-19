from unittest.mock import MagicMock, patch

import pytest

from core.deps import get_db


def test_get_db_yields_session_and_closes_on_completion():
    """Dependency should close the DB session when generator completes."""
    fake_session = MagicMock()

    with patch("core.deps.SessionLocal", return_value=fake_session):
        gen = get_db()
        yielded = next(gen)

        assert yielded is fake_session
        with pytest.raises(StopIteration):
            next(gen)

    fake_session.close.assert_called_once()


def test_get_db_closes_session_when_exception_is_thrown():
    """Dependency should close the DB session when request handling fails."""
    fake_session = MagicMock()

    with patch("core.deps.SessionLocal", return_value=fake_session):
        gen = get_db()
        yielded = next(gen)
        assert yielded is fake_session

        with pytest.raises(RuntimeError, match="dependency failure"):
            gen.throw(RuntimeError("dependency failure"))

    fake_session.close.assert_called_once()
