"""Debug lifecycle helpers.

Covers activation events: onDebug:*, onDebugResolve:*, onDebugAdapterProtocol:*
"""

import keyboard
from commands import run_command
from playwright.sync_api import Page


def start_debug(page: Page) -> None:
    """Start debugging (F5). Requires a launch.json or will prompt for config."""
    page.keyboard.press(keyboard.START_DEBUG)
    page.wait_for_timeout(2000)


def stop_debug(page: Page) -> None:
    """Stop the active debug session (Shift+F5)."""
    page.keyboard.press(keyboard.STOP_DEBUG)
    page.wait_for_timeout(500)


def step_over(page: Page) -> None:
    """Step over the current line in debugger (F10)."""
    page.keyboard.press(keyboard.STEP_OVER)
    page.wait_for_timeout(300)


def step_into(page: Page) -> None:
    """Step into the current function call in debugger (F11)."""
    page.keyboard.press(keyboard.STEP_INTO)
    page.wait_for_timeout(300)


def add_breakpoint_via_command(page: Page) -> None:
    """Toggle a breakpoint on the current line via Command Palette."""
    run_command(page, "Debug: Toggle Breakpoint")
    page.wait_for_timeout(300)


def create_launch_json(page: Page, debug_type: str = "node") -> None:
    """Create a launch.json configuration via Command Palette.

    Args:
        debug_type: The debug adapter type (e.g. "node", "python", "cppdbg").
    """
    run_command(
        page,
        "Debug: Open launch.json",
        expect_followup_quick_input=True,
    )
    page.wait_for_timeout(1000)
    # If quick-pick appears for selecting debug type, type and select
    page.keyboard.type(debug_type, delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)


def run_debug_session(page: Page, wait_ms: int = 5000) -> None:
    """Start debug, wait, then stop. Triggers full debug lifecycle events."""
    start_debug(page)
    page.wait_for_timeout(wait_ms)
    stop_debug(page)
