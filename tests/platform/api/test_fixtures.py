from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def client_without_test_engine(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
):
    conftest_module = next(
        plugin
        for plugin in request.config.pluginmanager.get_plugins()
        if Path(getattr(plugin, "__file__", "")).name == "conftest.py"
        and "tests/conftest.py" in str(getattr(plugin, "__file__", ""))
    )
    create_engine_spy = MagicMock(side_effect=AssertionError("test_engine was used"))
    monkeypatch.setattr(conftest_module, "create_engine", create_engine_spy)
    client = request.getfixturevalue("client")
    return client, create_engine_spy


def test_client_fixture_does_not_initialize_test_engine(client_without_test_engine):
    client, create_engine_spy = client_without_test_engine
    response = client.get("/health")

    assert response.status_code == 200
    create_engine_spy.assert_not_called()
