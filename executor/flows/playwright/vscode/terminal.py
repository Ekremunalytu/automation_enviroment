"""Integrated terminal helpers."""

from playwright.sync_api import Page

from ..vscode import keyboard
from .commands import run_command


def toggle_terminal(page: Page) -> None:
    """Toggle the integrated terminal panel."""
    page.keyboard.press(keyboard.TOGGLE_TERMINAL)
    page.wait_for_timeout(500)


def new_terminal(page: Page) -> None:
    """Create a new terminal instance via keyboard shortcut."""
    page.keyboard.press(keyboard.NEW_TERMINAL)
    page.wait_for_timeout(1000)


def new_terminal_via_command(page: Page) -> None:
    """Create a new terminal instance via Command Palette (fallback)."""
    run_command(page, "Terminal: Create New Terminal")
    page.wait_for_timeout(1000)


def type_in_terminal(page: Page, text: str, press_enter: bool = True) -> None:
    """Type text into the focused terminal and optionally press Enter.

    The terminal panel must already be open and focused.
    """
    page.keyboard.type(text, delay=20)
    if press_enter:
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)


def close_all_terminals(page: Page) -> None:
    """Kill every integrated terminal to stop them accumulating across attempts.

    Terminal/REPL-spawning commands (createTerminal, execInTerminal, startREPL,
    …) each leave a live terminal plus child processes behind. Across the many
    synthesized contributes-command attempts these pile up and feed
    renderer/host exhaustion. Running the built-in *Kill All Terminals* command
    between terminal-class attempts reclaims them. Coverage-neutral: the
    command already ran and was observed — only its leftover terminal is freed.
    """
    run_command(page, "Terminal: Kill All Terminals")
    page.wait_for_timeout(300)
