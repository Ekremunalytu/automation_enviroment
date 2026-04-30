"""Bottom panel helpers (Problems, Output, Debug Console)."""

import keyboard
from commands import run_command
from playwright.sync_api import Page


def toggle_panel(page: Page) -> None:
    """Toggle the bottom panel visibility."""
    page.keyboard.press(keyboard.TOGGLE_PANEL)
    page.wait_for_timeout(300)


def focus_problems(page: Page) -> None:
    """Focus the Problems tab via keyboard shortcut (Ctrl+Shift+M)."""
    page.keyboard.press(keyboard.FOCUS_PROBLEMS)
    page.wait_for_timeout(300)


def focus_output(page: Page) -> None:
    """Focus the Output tab via keyboard shortcut (Ctrl+Shift+U)."""
    page.keyboard.press(keyboard.FOCUS_OUTPUT)
    page.wait_for_timeout(300)


def open_problems(page: Page) -> None:
    """Open the Problems tab via Command Palette."""
    run_command(page, "View: Toggle Problems")
    page.wait_for_timeout(300)


def open_output(page: Page) -> None:
    """Open the Output tab via Command Palette."""
    run_command(page, "View: Toggle Output")
    page.wait_for_timeout(300)


def open_debug_console(page: Page) -> None:
    """Open the Debug Console tab in the bottom panel."""
    run_command(page, "View: Debug Console")
    page.wait_for_timeout(300)
