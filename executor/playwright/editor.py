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
