"""CDP connection and VS Code ready-state helpers."""

from __future__ import annotations

import contextlib
import os
import time
from collections.abc import Callable

from playwright.sync_api import Browser, Page, Playwright
from playwright.sync_api import Error as PlaywrightError

from ..stimulus.types import _HARNESS_READY_PATH

CDP_URL = f"http://localhost:{os.environ.get('EXECUTOR_CDP_PORT', '9222')}"

_DEFAULT_READY_TIMEOUT_MS = 10_000
DEFAULT_RECONNECT_TIMEOUT_MS = 60_000
_DEFAULT_RELOAD_TEARDOWN_WAIT_MS = 3_000
_DEFAULT_EXTENSION_SETTLE_MS = 5_000

ReloadLogger = Callable[[str], None] | None


class ReloadWindowError(RuntimeError):
    """Raised when VS Code reload cannot be verified through the CDP path."""

    def __init__(self, phase: str, detail: str) -> None:
        super().__init__(f"{phase}: {detail}")
        self.phase = phase
        self.detail = detail


def _emit_reload_log(log: ReloadLogger, phase: str, detail: str) -> None:
    if log is None:
        return
    log(f"[reload] {phase}: {detail}")


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
    timeout_ms: int = DEFAULT_RECONNECT_TIMEOUT_MS,
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


def connect_to_ready_workbench(
    playwright: Playwright,
    *,
    timeout_ms: int = DEFAULT_RECONNECT_TIMEOUT_MS,
    log: ReloadLogger = None,
) -> tuple[Browser, Page]:
    """Connect to CDP and return a ready VS Code workbench page."""
    _emit_reload_log(log, "connect", f"Connecting to VS Code over CDP at {CDP_URL}...")
    try:
        browser = playwright.chromium.connect_over_cdp(CDP_URL, timeout=timeout_ms)
    except PlaywrightError as exc:
        raise ReloadWindowError(
            "connect",
            f"Could not connect to VS Code over CDP at {CDP_URL}: {exc}",
        ) from exc

    try:
        page = reconnect_to_workbench(browser, timeout_ms=timeout_ms)
    except RuntimeError as exc:
        raise ReloadWindowError("connect", str(exc)) from exc

    _emit_reload_log(
        log,
        "connect",
        f"Connected to ready workbench page {_page_diagnostic(page)}.",
    )
    return browser, page


def wait_until_ready(page: Page, timeout_ms: int = 10_000) -> None:
    """Wait until the VS Code workbench is fully loaded."""
    page.wait_for_selector(".monaco-workbench", state="visible", timeout=timeout_ms)


def reload_workbench_window(
    browser: Browser,
    page: Page,
    *,
    pre_ready_timeout_ms: int = _DEFAULT_READY_TIMEOUT_MS,
    reconnect_timeout_ms: int = DEFAULT_RECONNECT_TIMEOUT_MS,
    teardown_wait_ms: int = _DEFAULT_RELOAD_TEARDOWN_WAIT_MS,
    extension_settle_ms: int = _DEFAULT_EXTENSION_SETTLE_MS,
    log: ReloadLogger = None,
) -> Page:
    """Reload a VS Code workbench page and verify the replacement window."""
    _emit_reload_log(log, "pre_ready", "Waiting for VS Code workbench before reload...")
    try:
        wait_until_ready(page, timeout_ms=pre_ready_timeout_ms)
    except PlaywrightError as exc:
        raise ReloadWindowError(
            "pre_ready",
            f"VS Code workbench was not ready before reload: {exc}",
        ) from exc

    _emit_reload_log(log, "dispatch", "Sending 'Developer: Reload Window' command...")
    # Clear the harness ready marker so post-reload polling can only succeed
    # once the new extension activation writes a fresh marker. Without this,
    # a stale marker from the prior activation would let the next harness
    # command race ahead before the command is registered.
    with contextlib.suppress(FileNotFoundError):
        _HARNESS_READY_PATH.unlink()
    try:
        from . import commands

        commands.run_reload_window_command(page)
    except PlaywrightError as exc:
        raise ReloadWindowError(
            "dispatch",
            f"Could not dispatch the reload command: {exc}",
        ) from exc

    _emit_reload_log(
        log,
        "reconnect",
        f"Waiting {teardown_wait_ms}ms for VS Code to tear down before reconnect...",
    )
    try:
        page.wait_for_timeout(teardown_wait_ms)
    except PlaywrightError as exc:
        raise ReloadWindowError(
            "reconnect",
            f"VS Code page became unreachable during reload teardown: {exc}",
        ) from exc

    _emit_reload_log(log, "reconnect", "Reconnecting to a ready VS Code workbench...")
    try:
        reloaded_page = reconnect_to_workbench(
            browser,
            preferred_page=page,
            timeout_ms=reconnect_timeout_ms,
        )
    except RuntimeError as exc:
        raise ReloadWindowError("reconnect", str(exc)) from exc

    page_kind = "preferred" if reloaded_page is page else "fallback"
    _emit_reload_log(
        log,
        "reconnect",
        f"Connected to the {page_kind} workbench page.",
    )

    _emit_reload_log(
        log,
        "post_settle",
        f"Waiting {extension_settle_ms}ms for extensions to settle after reload...",
    )
    try:
        reloaded_page.wait_for_timeout(extension_settle_ms)
    except PlaywrightError as exc:
        raise ReloadWindowError(
            "post_settle",
            f"VS Code did not remain stable after reload: {exc}",
        ) from exc

    _emit_reload_log(log, "done", "VS Code reload completed.")
    return reloaded_page


def disconnect(browser: Browser) -> None:
    """Close the CDP connection."""
    browser.close()
