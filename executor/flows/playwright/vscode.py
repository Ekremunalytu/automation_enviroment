"""CDP connection and VS Code ready-state helpers."""

from __future__ import annotations

import os
import time

from playwright.sync_api import Browser, Page, Playwright
from playwright.sync_api import Error as PlaywrightError

CDP_URL = f"http://localhost:{os.environ.get('EXECUTOR_CDP_PORT', '9222')}"


def _page_title(page: Page) -> str:
    try:
        return str(page.title() or "")
    except PlaywrightError:
        return ""


def _page_url(page: Page) -> str:
    return str(getattr(page, "url", "") or "")


def _page_diagnostic(page: Page) -> str:
    url = _page_url(page)
    if not url:
        return "title='' url=''"
    title = _page_title(page)
    if title:
        return f"title={title!r} url={url!r}"
    return f"url={url!r}"


def find_workbench_page(browser: Browser) -> Page:
    non_devtools_pages: list[Page] = []

    for context in browser.contexts:
        for page in context.pages:
            url = _page_url(page)
            if url.startswith("devtools://"):
                continue
            if url.startswith("vscode-file://") and "workbench.html" in url:
                return page
            non_devtools_pages.append(page)

    for page in non_devtools_pages:
        if "Visual Studio Code" in _page_title(page):
            return page

    for page in non_devtools_pages:
        if _page_url(page).startswith("vscode-file://"):
            return page

    discovered = [
        _page_diagnostic(page) for context in browser.contexts for page in context.pages
    ]

    discovered_pages = (
        ", ".join(discovered) if discovered else "no CDP pages discovered"
    )
    raise RuntimeError(
        "Could not find a VS Code workbench page via CDP. "
        f"Discovered pages: {discovered_pages}"
    )


def reconnect_to_workbench(
    browser: Browser,
    *,
    preferred_page: Page | None = None,
    timeout_ms: int = 30_000,
    probe_timeout_ms: int = 2_000,
    poll_interval_ms: int = 250,
) -> Page:
    """Reconnect to a ready VS Code workbench page after a reload."""
    deadline = time.monotonic() + (timeout_ms / 1000)
    last_error = "workbench page not yet available"

    while time.monotonic() < deadline:
        remaining_ms = max(int((deadline - time.monotonic()) * 1000), 1)
        candidate_pages: list[Page] = []
        if preferred_page is not None:
            candidate_pages.append(preferred_page)
        try:
            candidate_pages.append(find_workbench_page(browser))
        except RuntimeError as exc:
            last_error = str(exc)

        seen_pages: set[int] = set()
        for candidate in candidate_pages:
            candidate_id = id(candidate)
            if candidate_id in seen_pages:
                continue
            seen_pages.add(candidate_id)
            try:
                wait_until_ready(
                    candidate,
                    timeout_ms=min(probe_timeout_ms, remaining_ms),
                )
                return candidate
            except PlaywrightError as exc:
                last_error = str(exc)

        time.sleep(min(poll_interval_ms, remaining_ms) / 1000)

    raise RuntimeError(
        "Timed out while reconnecting to a VS Code workbench page. "
        f"Last observed error: {last_error}"
    )


def connect(playwright: Playwright) -> tuple[Browser, Page]:
    """Connect to VS Code over CDP and return (browser, page)."""
    browser = playwright.chromium.connect_over_cdp(CDP_URL)
    return browser, find_workbench_page(browser)


def wait_until_ready(page: Page, timeout_ms: int = 10_000) -> None:
    """Wait until the VS Code workbench is fully loaded."""
    page.wait_for_selector(".monaco-workbench", state="visible", timeout=timeout_ms)


def disconnect(browser: Browser) -> None:
    """Close the CDP connection."""
    browser.close()
