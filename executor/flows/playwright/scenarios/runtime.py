"""Runtime and integration-heavy Playwright automation scenarios."""

from __future__ import annotations

import commands
import debug
import editor
import panel
import sidebar
import terminal

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .common import log


def scenario_debug_session(page: Page) -> None:
    """Simulate a debugging workflow."""
    log("Debug session")

    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)
    sidebar.open_debug(page)
    page.wait_for_timeout(500)
    page.keyboard.press("Control+Home")
    for _ in range(10):
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(200)
    debug.add_breakpoint_via_command(page)
    page.wait_for_timeout(300)
    debug.start_debug(page)
    page.wait_for_timeout(3000)
    editor._dismiss_notification(page)
    page.wait_for_timeout(300)
    debug.step_over(page)
    page.wait_for_timeout(500)
    debug.step_over(page)
    page.wait_for_timeout(500)
    panel.open_debug_console(page)
    page.wait_for_timeout(500)
    debug.stop_debug(page)
    page.wait_for_timeout(500)
    editor._dismiss_notification(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def scenario_terminal_usage(page: Page) -> None:
    """Simulate developer terminal activity."""
    log("Terminal usage")

    terminal.new_terminal(page)
    page.wait_for_timeout(1000)
    for cmd in [
        "ls -la",
        "cat .env",
        "git status",
        "python --version",
        "node --version",
        "pip list",
        "npm ls --depth=0",
        "echo $PATH",
    ]:
        terminal.type_in_terminal(page, cmd)
        page.wait_for_timeout(1500)
    terminal.new_terminal(page)
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "pwd")
    page.wait_for_timeout(500)


def scenario_git_workflow(page: Page) -> None:
    """Simulate a git workflow via sidebar and terminal."""
    log("Git workflow")

    sidebar.open_source_control(page)
    page.wait_for_timeout(1000)
    editor.open_file_by_name(page, "README.md")
    page.wait_for_timeout(500)
    page.keyboard.press("Control+End")
    editor.type_in_editor(page, "\n## Updated section\nNew content here.\n")
    editor.save_file(page)
    page.wait_for_timeout(500)
    sidebar.open_source_control(page)
    page.wait_for_timeout(1000)
    terminal.toggle_terminal(page)
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "git --no-pager diff")
    page.wait_for_timeout(1000)
    terminal.type_in_terminal(page, "git add -A")
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "git status")
    page.wait_for_timeout(500)
    terminal.toggle_terminal(page)


def scenario_authentication_probe(page: Page) -> None:
    """Exercise VS Code account and sign-in flows."""
    log("Authentication probe")

    commands.run_command(
        page,
        "Accounts: Sign In",
        expect_followup_quick_input=True,
    )
    page.wait_for_timeout(1500)
    editor._dismiss_notification(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def scenario_webview_probe(page: Page) -> None:
    """Exercise a built-in preview surface backed by a webview."""
    log("Webview probe")

    editor.open_file_by_name(page, "README.md")
    page.wait_for_timeout(1000)
    commands.run_command(page, "Markdown: Open Preview")
    page.wait_for_timeout(1500)
    try:
        webview_frame = page.locator("iframe.webview, .webview, .webview-element").first
        if webview_frame.is_visible(timeout=1000):
            webview_frame.click()
            page.wait_for_timeout(300)
    except PlaywrightError:
        pass
    editor.close_active_editor(page)
    page.wait_for_timeout(400)
    editor.close_active_editor(page)
    page.wait_for_timeout(300)
