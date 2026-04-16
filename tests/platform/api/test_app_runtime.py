from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

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
            match=(
                "Marketplace analysis job storage is unavailable; run migrations "
                "and verify DB connectivity before starting the API."
            ),
        ) as exc_info,
    ):
        main.create_app()

    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)
