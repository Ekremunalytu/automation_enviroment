from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _no_real_sleep_in_wait_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep wait-helper settles instant in unit tests.

    The command/trigger effect settles sleep host-side (``page=None`` ->
    ``time.sleep``) in production so they don't balloon in renderer time under
    load. A unit test must never block on that real sleep. This shim preserves
    the fake-page path (tests that record ``page.wait_for_timeout`` calls keep
    working) while dropping the host-side ``time.sleep`` entirely. Tests that
    need to observe the ``_wait`` calls themselves re-patch it explicitly.
    """
    from executor.flows.playwright import wait_helpers

    def _fast_wait(page: Any, timeout_ms: int) -> None:
        if page is not None and hasattr(page, "wait_for_timeout"):
            page.wait_for_timeout(timeout_ms)

    monkeypatch.setattr(wait_helpers, "_wait", _fast_wait)


@pytest.fixture(autouse=True)
def _harness_python_secret_env_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W13-11: clear EXECUTOR_HARNESS_PYTHON_SECRET_VALUE for every executor test.

    Production sets this env var on the docker exec child process only; no
    test should inherit it from the harness shell, and any test that needs
    to assert env-priority behavior must opt in explicitly via
    ``monkeypatch.setenv``. Without this fixture, a CI runner with the
    var pre-set would silently flip
    ``executor.flows.playwright.health.reconciliation.load_harness_python_secret``
    into env-priority mode and the legacy-file unit cases would assert
    against the wrong branch.
    """
    monkeypatch.delenv("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", raising=False)


if "playwright.sync_api" not in sys.modules:
    playwright_module = ModuleType("playwright")
    sync_api_module = ModuleType("playwright.sync_api")

    class _DummyPage:
        pass

    class _DummyBrowser:
        pass

    class _DummyPlaywright:
        pass

    class _DummyPlaywrightError(Exception):
        pass

    class _DummyPlaywrightTimeoutError(Exception):
        pass

    def _sync_playwright():
        raise RuntimeError("playwright is not available in unit tests")

    sync_api_module.Page = _DummyPage
    sync_api_module.Browser = _DummyBrowser
    sync_api_module.Playwright = _DummyPlaywright
    sync_api_module.Error = _DummyPlaywrightError
    sync_api_module.TimeoutError = _DummyPlaywrightTimeoutError
    sync_api_module.sync_playwright = _sync_playwright
    playwright_module.sync_api = sync_api_module
    sys.modules["playwright"] = playwright_module
    sys.modules["playwright.sync_api"] = sync_api_module
