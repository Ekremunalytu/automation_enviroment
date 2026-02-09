"""Bottom panel helpers (Problems, Output, Debug Console)."""

import keyboard
from commands import run_command
from playwright.sync_api import Page


def toggle_panel(page: Page) -> None:
    """Toggle the bottom panel visibility."""
    page.keyboard.press(keyboard.TOGGLE_PANEL)
    page.wait_for_timeout(300)


def open_problems(page: Page) -> None:
    """Open the Problems tab in the bottom panel."""
    run_command(page, "View: Toggle Problems")
    page.wait_for_timeout(300)


def open_output(page: Page) -> None:
    """Open the Output tab in the bottom panel."""
    run_command(page, "View: Toggle Output")
    page.wait_for_timeout(300)


def open_debug_console(page: Page) -> None:
    """Open the Debug Console tab in the bottom panel."""
    run_command(page, "View: Debug Console")
    page.wait_for_timeout(300)
