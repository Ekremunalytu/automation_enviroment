"""Editor operations via UI.

Covers activation events: onLanguage:*, onCustomEditor:*
"""

import subprocess

import keyboard
from commands import quick_open, run_command

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def new_untitled_file(page: Page) -> None:
    """Create a new untitled editor tab."""
    page.keyboard.press(keyboard.NEW_FILE)
    page.wait_for_timeout(500)


def save_file(page: Page) -> None:
    """Save the active file (Ctrl+S). Only works if file already has a path."""
    page.keyboard.press(keyboard.SAVE_FILE)
    page.wait_for_timeout(500)


def save_file_as(page: Page, filename: str) -> None:
    """Trigger Save-As via native GTK dialog.

    Ctrl+Shift+S opens a native OS file dialog that Playwright cannot see.
    We use xdotool to type the filename and press the Save button.
    """
    page.keyboard.press(keyboard.SAVE_FILE_AS)
    page.wait_for_timeout(1500)  # wait for native dialog to appear

    # Clear existing filename in the dialog, type new one, press Enter
    # nosec B603,B607: xdotool with fixed arguments, filename is internal
    # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
    subprocess.run(["xdotool", "key", "ctrl+a"], check=True)  # nosec B603,B607
    # arch-allow: bare-binary-path
    subprocess.run(["xdotool", "type", "--delay", "30", filename], check=True)  # nosec B603,B607
    page.wait_for_timeout(300)
    # arch-allow: bare-binary-path
    subprocess.run(["xdotool", "key", "Return"], check=True)  # nosec B603,B607
    page.wait_for_timeout(1000)


def close_active_editor(page: Page) -> None:
    """Close the currently active editor tab."""
    page.keyboard.press(keyboard.CLOSE_EDITOR)
    page.wait_for_timeout(300)


def type_in_editor(page: Page, text: str) -> None:
    """Type text into the active editor."""
    page.keyboard.press(keyboard.FOCUS_EDITOR)
    page.wait_for_timeout(200)
    page.keyboard.type(text, delay=10)


def open_file_by_name(page: Page, filename: str) -> None:
    """Open a file using Quick Open (Ctrl+P)."""
    quick_open(page, filename)


def close_all_editors(page: Page) -> None:
    """Close all open editor tabs via chord shortcut."""
    run_command(page, "View: Close All Editors")
    page.wait_for_timeout(300)


def format_document(page: Page) -> None:
    """Format the active document (Ctrl+Shift+I).

    Triggers formatter extensions (e.g. Prettier, Black).
    If no formatter is installed, VS Code shows a notification dialog
    ("No formatter for X files installed") which we dismiss.
    """
    page.keyboard.press(keyboard.FORMAT_DOCUMENT)
    page.wait_for_timeout(1000)
    _dismiss_notification(page)


def go_to_definition(page: Page) -> None:
    """Go to definition of symbol under cursor (F12).

    Triggers language server / definition provider extensions.
    """
    page.keyboard.press(keyboard.GO_TO_DEFINITION)
    page.wait_for_timeout(1000)


def trigger_suggest(page: Page) -> None:
    """Trigger IntelliSense suggestions (Ctrl+Space).

    Triggers completion provider extensions.
    """
    page.keyboard.press(keyboard.TRIGGER_SUGGEST)
    page.wait_for_timeout(1000)


def rename_symbol(page: Page, new_name: str) -> None:
    """Rename the symbol under cursor (F2).

    Triggers rename provider extensions.

    Args:
        new_name: The new name for the symbol.
    """
    page.keyboard.press(keyboard.RENAME_SYMBOL)
    page.wait_for_timeout(500)
    # Clear existing name and type new one
    page.keyboard.press(keyboard.SELECT_ALL)
    page.keyboard.type(new_name, delay=20)
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)


def select_all(page: Page) -> None:
    """Select all text in the active editor (Ctrl+A)."""
    page.keyboard.press(keyboard.SELECT_ALL)
    page.wait_for_timeout(200)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_NOTIFICATION_SELECTORS = [
    ".notification-toast",
    ".notifications-toasts .notification-toast",
]


def _dismiss_notification(page: Page) -> str:
    """Dismiss any visible VS Code notification toast.

    VS Code shows notification dialogs (e.g. 'No formatter installed',
    'Install Extension') as toast elements. These block subsequent
    operations if not dismissed.  We try clicking the close button
    first; if that fails we press Escape.
    """
    for selector in _NOTIFICATION_SELECTORS:
        try:
            toast = page.wait_for_selector(selector, state="visible", timeout=800)
            if toast is None:
                continue
            toast_text = toast.inner_text().strip()
            # Try clicking the dismiss/close button on the toast
            close_btn = toast.query_selector(
                ".codicon-notifications-clear, .codicon-close"
            )
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(300)
                return toast_text or "notification toast"
            # Fallback: click Cancel button if present
            cancel_btn = toast.query_selector("a.action-label[title='Cancel']")
            if cancel_btn:
                cancel_btn.click()
                page.wait_for_timeout(300)
                return toast_text or "notification toast"
        except PlaywrightTimeoutError:
            continue
    # Last resort: Escape to dismiss anything lingering
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    return ""
