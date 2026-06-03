from __future__ import annotations

import importlib
import re
import sys
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError


def _load_main_module():
    main_module = sys.modules.get("main")
    if main_module is not None:
        return main_module

    from workflows.marketplace import job_service

    with patch(
        "workflows.marketplace.job_service.recover_interrupted_jobs",
        return_value=0,
    ):
        main_module = importlib.import_module("main")

    main_module.recover_interrupted_jobs = job_service.recover_interrupted_jobs
    return main_module


def test_create_app_recovers_interrupted_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    main = _load_main_module()
    monkeypatch.setattr(main.settings.api, "WORKERS", 1)

    with patch("main.recover_interrupted_jobs") as recover_jobs:
        app = main.create_app()

    assert app.title == main.settings.project.NAME
    recover_jobs.assert_called_once_with()


def test_create_app_rejects_multiple_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = _load_main_module()
    monkeypatch.setattr(main.settings.api, "WORKERS", 2)

    with pytest.raises(RuntimeError, match="API_WORKERS=1"):
        main.create_app()


def test_create_app_fails_fast_when_job_storage_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = _load_main_module()
    monkeypatch.setattr(main.settings.api, "WORKERS", 1)

    with (
        patch(
            "main.recover_interrupted_jobs",
            side_effect=SQLAlchemyError("migration missing"),
        ),
        pytest.raises(
            RuntimeError,
            match=re.escape(
                "Marketplace analysis job storage is unavailable; run migrations "
                "and verify DB connectivity before starting the API."
            ),
        ) as exc_info,
    ):
        main.create_app()

    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)


def test_prime_blacklist_override_swallows_db_error() -> None:
    """A DB failure while priming the operator denylist never blocks startup.

    ``prime_blacklist_override`` runs unconditionally in ``create_app``; the
    dynamic ``a7`` rule falls back to the shipped seed when the operator DB is
    unreachable (or the ``blacklist_domains`` table is not yet migrated), so the
    priming failure must be swallowed. Covers the ``except SQLAlchemyError`` path
    — and asserts the session is still closed on the error route.
    """
    main = _load_main_module()
    fake_session = MagicMock()

    with (
        patch("appcore.db.session.SessionLocal", return_value=fake_session),
        patch(
            "workflows.detection_rules.blacklist_service.refresh_operator_override",
            side_effect=SQLAlchemyError("blacklist_domains table missing"),
        ),
    ):
        # Must not raise.
        main.prime_blacklist_override()

    fake_session.close.assert_called_once_with()


def test_prime_blacklist_override_refreshes_then_closes_session() -> None:
    """Happy path: open a session, refresh the matcher override, close the session."""
    main = _load_main_module()
    fake_session = MagicMock()

    with (
        patch(
            "appcore.db.session.SessionLocal", return_value=fake_session
        ) as session_local,
        patch(
            "workflows.detection_rules.blacklist_service.refresh_operator_override"
        ) as refresh,
    ):
        main.prime_blacklist_override()

    session_local.assert_called_once_with()
    refresh.assert_called_once_with(fake_session)
    fake_session.close.assert_called_once_with()
