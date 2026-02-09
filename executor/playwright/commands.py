"""Command Palette helpers.

Covers activation events: onCommand:*
"""

import keyboard
from playwright.sync_api import Page

# VS Code keeps .quick-input-widget in the DOM but toggles a style attribute.
# When visible:  style="..." (no display:none)
# When hidden:   style="display: none;"
_QUICK_INPUT_VISIBLE = ".quick-input-widget:not([style*='display: none'])"


def _wait_quick_input_open(page: Page, timeout_ms: int = 3000) -> None:
    """Wait until the quick-input widget becomes visible."""
    page.wait_for_selector(_QUICK_INPUT_VISIBLE, state="attached", timeout=timeout_ms)


def _wait_quick_input_close(page: Page, timeout_ms: int = 5000) -> None:
    """Wait until the quick-input widget is hidden (display: none)."""
    page.wait_for_selector(_QUICK_INPUT_VISIBLE, state="detached", timeout=timeout_ms)


def open_command_palette(page: Page) -> None:
    """Open the VS Code Command Palette."""
    page.keyboard.press(keyboard.COMMAND_PALETTE)
    _wait_quick_input_open(page)


def run_command(page: Page, command_text: str) -> None:
    """Open Command Palette, type a command, and execute it."""
    open_command_palette(page)
    page.keyboard.type(command_text, delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    _wait_quick_input_close(page)


def quick_open(page: Page, query: str) -> None:
    """Open Quick Open (Ctrl+P), type a query, and press Enter."""
    page.keyboard.press(keyboard.QUICK_OPEN)
    _wait_quick_input_open(page)
    page.keyboard.type(query, delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    _wait_quick_input_close(page)
