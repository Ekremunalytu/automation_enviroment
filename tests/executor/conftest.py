from __future__ import annotations

import sys
from types import ModuleType

import pytest


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


@pytest.fixture(scope="session", autouse=True)
def check_database_connection() -> None:
    """Override global DB gate for DB-independent executor unit tests."""
    return None
