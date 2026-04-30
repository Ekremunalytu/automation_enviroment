"""Sidebar and Activity Bar helpers.

Covers activation events: onView:*
"""

import keyboard
from commands import run_command
from playwright.sync_api import Page


def toggle_sidebar(page: Page) -> None:
    """Toggle the sidebar visibility."""
    page.keyboard.press(keyboard.TOGGLE_SIDEBAR)
    page.wait_for_timeout(300)


def open_explorer(page: Page) -> None:
    """Focus the Explorer view in the sidebar."""
    page.keyboard.press(keyboard.FOCUS_EXPLORER)
    page.wait_for_timeout(300)


def open_search(page: Page) -> None:
    """Focus the Search view in the sidebar."""
    page.keyboard.press(keyboard.FOCUS_SEARCH)
    page.wait_for_timeout(300)


def open_source_control(page: Page) -> None:
    """Focus the Source Control view in the sidebar."""
    page.keyboard.press(keyboard.FOCUS_SOURCE_CONTROL)
    page.wait_for_timeout(300)


def open_debug(page: Page) -> None:
    """Focus the Run and Debug view in the sidebar."""
    page.keyboard.press(keyboard.FOCUS_DEBUG)
    page.wait_for_timeout(300)


def open_extensions_view(page: Page) -> None:
    """Focus the Extensions view in the sidebar."""
    page.keyboard.press(keyboard.FOCUS_EXTENSIONS)
    page.wait_for_timeout(300)


def open_view_by_command(page: Page, view_name: str) -> None:
    """Open an arbitrary view via Command Palette (e.g. custom viewContainers)."""
    run_command(page, f"View: Show {view_name}")
    page.wait_for_timeout(300)
