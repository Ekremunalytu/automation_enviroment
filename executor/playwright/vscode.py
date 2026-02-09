"""CDP connection and VS Code ready-state helpers."""

import os

from playwright.sync_api import Browser, Page, Playwright

CDP_URL = f"http://localhost:{os.environ.get('EXECUTOR_CDP_PORT', '9222')}"


def connect(playwright: Playwright) -> tuple[Browser, Page]:
    """Connect to VS Code over CDP and return (browser, page)."""
    browser = playwright.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    page = context.pages[0]
    return browser, page


def wait_until_ready(page: Page, timeout_ms: int = 10_000) -> None:
    """Wait until the VS Code workbench is fully loaded."""
    page.wait_for_selector(".monaco-workbench", state="visible", timeout=timeout_ms)


def disconnect(browser: Browser) -> None:
    """Close the CDP connection."""
    browser.close()
