"""Editor operations via UI.

Covers activation events: onLanguage:*, onCustomEditor:*
"""

import subprocess

import keyboard
from commands import quick_open, run_command
from playwright.sync_api import Page


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
    subprocess.run(["xdotool", "key", "ctrl+a"], check=True)  # nosec B603,B607
    subprocess.run(["xdotool", "type", "--delay", "30", filename], check=True)  # nosec B603,B607
    page.wait_for_timeout(300)
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
    """
    page.keyboard.press(keyboard.FORMAT_DOCUMENT)
    page.wait_for_timeout(1000)


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
