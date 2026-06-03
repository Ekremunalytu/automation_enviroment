"""Command Palette helpers.

Covers activation events: onCommand:*
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ..vscode import keyboard

_QUICK_INPUT_VISIBLE = ".quick-input-widget:not([style*='display: none'])"
_QUICK_INPUT_INPUT_SELECTORS = (
    f"{_QUICK_INPUT_VISIBLE} input.input",
    f"{_QUICK_INPUT_VISIBLE} .monaco-inputbox input",
    f"{_QUICK_INPUT_VISIBLE} input[type='text']",
)
# W22 Fix 2 makes Save As / Open / message dialogs render inside the workbench
# DOM (``window.dialogStyle: custom``); this is the Monaco dialog container the
# follow-up drain (Fix 3) backs out of with Escape.
_CUSTOM_DIALOG_VISIBLE = ".monaco-dialog-box"
_FOLLOWUP_UI_SELECTORS = (_QUICK_INPUT_VISIBLE, _CUSTOM_DIALOG_VISIBLE)


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


def _selector_visible(page: Page, selector: str) -> bool:
    """Instant (non-waiting) visibility check for a follow-up UI surface."""
    try:
        handle = page.query_selector(selector)
    except PlaywrightError:
        return False
    if handle is None:
        return False
    try:
        return bool(handle.is_visible())
    except PlaywrightError:
        return False


def drain_followup_ui(page: Page, *, max_depth: int = 2) -> int:
    """Back out of follow-up quick-inputs / dialogs a command opened.

    Some commands open a QuickPick, InputBox, or (with Fix 2's in-renderer
    dialogs) a Save As / message dialog *after* invocation. Activation has
    already fired by the time we reach here, so the policy is to back out
    cleanly with Escape — not to complete a file-writing flow — so the next
    layered attempt is not blocked behind a lingering modal. Bounded by
    ``max_depth`` so a surface that refuses to close cannot spin the loop.
    Returns the number of layers dismissed.
    """
    dismissed = 0
    for _ in range(max(0, max_depth)):
        if not any(_selector_visible(page, sel) for sel in _FOLLOWUP_UI_SELECTORS):
            break
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        dismissed += 1
    return dismissed


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
