"""Command Palette helpers.

Covers activation events: onCommand:*
"""

import keyboard

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

_QUICK_INPUT_VISIBLE = ".quick-input-widget:not([style*='display: none'])"
_QUICK_INPUT_INPUT_SELECTORS = (
    f"{_QUICK_INPUT_VISIBLE} input.input",
    f"{_QUICK_INPUT_VISIBLE} .monaco-inputbox input",
    f"{_QUICK_INPUT_VISIBLE} input[type='text']",
)


class CommandPaletteUnavailableError(RuntimeError):
    """Raised when VS Code quick input cannot be opened or stabilized."""

    def __init__(self, reason_code: str, detail: str):
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code


def _focus_workbench(page: Page) -> None:
    """Clear transient UI so the next quick-input shortcut lands reliably."""
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    page.keyboard.press(keyboard.FOCUS_EDITOR)
    page.wait_for_timeout(150)


def _wait_quick_input_ready(page: Page, timeout_ms: int = 3000) -> None:
    """Wait until the quick-input widget and its text input are visible."""
    try:
        page.wait_for_selector(
            _QUICK_INPUT_VISIBLE, state="visible", timeout=timeout_ms
        )
    except PlaywrightTimeoutError as exc:
        raise CommandPaletteUnavailableError(
            "quick_input_unavailable",
            "Quick input container did not become visible.",
        ) from exc

    for selector in _QUICK_INPUT_INPUT_SELECTORS:
        try:
            page.wait_for_selector(selector, state="visible", timeout=800)
            return
        except PlaywrightTimeoutError:
            continue

    raise CommandPaletteUnavailableError(
        "quick_input_input_unavailable",
        "Quick input opened without a visible input field.",
    )


def _wait_quick_input_hidden(page: Page, timeout_ms: int = 5000) -> None:
    """Wait until no visible quick-input widget remains on screen."""
    try:
        page.wait_for_selector(_QUICK_INPUT_VISIBLE, state="hidden", timeout=timeout_ms)
        return
    except PlaywrightTimeoutError:
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
    try:
        page.wait_for_selector(_QUICK_INPUT_VISIBLE, state="hidden", timeout=1000)
    except PlaywrightTimeoutError as exc:
        raise CommandPaletteUnavailableError(
            "quick_input_did_not_close",
            "Quick input remained visible after command execution.",
        ) from exc


def wait_for_quick_input_hidden(page: Page, timeout_ms: int = 5000) -> None:
    """Public wrapper for flows that need to close a follow-up picker."""
    _wait_quick_input_hidden(page, timeout_ms=timeout_ms)


def open_quick_input(page: Page, mode: str) -> None:
    """Open a VS Code quick-input surface with a retry around focus cleanup."""
    shortcut = {
        "command_palette": keyboard.COMMAND_PALETTE,
        "quick_open": keyboard.QUICK_OPEN,
    }.get(mode)
    if not shortcut:
        raise ValueError(f"Unsupported quick-input mode: {mode}")

    last_error: CommandPaletteUnavailableError | None = None
    for _ in range(2):
        _focus_workbench(page)
        page.keyboard.press(shortcut)
        page.wait_for_timeout(200)
        try:
            _wait_quick_input_ready(page)
            return
        except CommandPaletteUnavailableError as exc:
            last_error = exc
            page.keyboard.press("Escape")
            page.wait_for_timeout(250)

    reason_code = f"{mode}_unavailable"
    detail = (
        str(last_error) if last_error is not None else f"{mode} could not be opened."
    )
    raise CommandPaletteUnavailableError(reason_code, detail)


def open_command_palette(page: Page) -> None:
    """Open the VS Code Command Palette."""
    open_quick_input(page, "command_palette")


def run_command(
    page: Page,
    command_text: str,
    *,
    expect_followup_quick_input: bool = False,
) -> None:
    """Open Command Palette, type a command, and execute it."""
    open_command_palette(page)
    page.keyboard.type(command_text, delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    if expect_followup_quick_input:
        _wait_quick_input_ready(page, timeout_ms=4000)
        return
    _wait_quick_input_hidden(page)


def run_reload_window_command(page: Page) -> None:
    """Dispatch the reload command without waiting for quick-input teardown."""
    open_command_palette(page)
    page.keyboard.type("Developer: Reload Window", delay=30)
    page.wait_for_timeout(500)
    try:
        page.keyboard.press("Enter")
    except PlaywrightError:
        return


def quick_open(page: Page, query: str) -> None:
    """Open Quick Open (Ctrl+P), type a query, and press Enter."""
    open_quick_input(page, "quick_open")
    page.keyboard.type(query, delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    _wait_quick_input_hidden(page)
