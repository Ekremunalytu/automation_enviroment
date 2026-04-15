from __future__ import annotations

from unittest.mock import patch

import pytest

import main


def test_create_app_recovers_interrupted_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main.settings.api, "WORKERS", 1)

    with patch("main.recover_interrupted_jobs") as recover_jobs:
        app = main.create_app()

    assert app.title == main.settings.project.NAME
    recover_jobs.assert_called_once_with()


def test_create_app_rejects_multiple_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main.settings.api, "WORKERS", 2)

    with pytest.raises(RuntimeError, match="API_WORKERS=1"):
        main.create_app()
