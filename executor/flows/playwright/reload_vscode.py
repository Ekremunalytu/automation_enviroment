"""
Reload VS Code window via CDP after extension installation.

This script is executed inside the executor container via ``docker exec``
after ``code --install-extension`` so that VS Code picks up the newly
installed extension.  Without a reload, the extension never activates.

Usage (from host):
    docker exec automation_executor python3 \
        /home/executor/flows/playwright/reload_vscode.py
"""

import sys
from pathlib import Path

# Bootstrap: add parent dir so sibling imports resolve correctly.
_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import commands  # noqa: E402
import vscode  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

_RELOAD_TIMEOUT_MS = 30_000
"""Maximum time (ms) to wait for workbench to become ready after reload."""


def reload_window() -> None:
    """Connect to VS Code via CDP, reload the window, wait until ready."""
    with sync_playwright() as pw:
        print("[reload] Connecting to VS Code...")
        browser = pw.chromium.connect_over_cdp(vscode.CDP_URL)
        page = vscode.reconnect_to_workbench(
            browser,
            timeout_ms=_RELOAD_TIMEOUT_MS,
        )

        print("[reload] Waiting for VS Code to be ready (pre-reload)...")
        vscode.wait_until_ready(page)

        print("[reload] Sending 'Developer: Reload Window' command...")
        commands.run_reload_window_command(page)

        # After reload the page navigates; wait for the workbench to reappear.
        print("[reload] Waiting for VS Code workbench after reload...")
        page.wait_for_timeout(3000)  # give VS Code time to tear down

        try:
            reloaded_page = vscode.reconnect_to_workbench(
                browser,
                preferred_page=page,
                timeout_ms=_RELOAD_TIMEOUT_MS,
            )
            if reloaded_page is page:
                print("[reload] VS Code reloaded successfully ✓")
            else:
                print("[reload] VS Code reloaded successfully (fallback) ✓")
                page = reloaded_page
        except RuntimeError as exc:
            print(f"[reload] WARNING: Could not verify reload completed ({exc})")

        # Extra wait for extensions to finish activating after reload.
        page.wait_for_timeout(5000)

        vscode.disconnect(browser)
        print("[reload] Done")


if __name__ == "__main__":
    reload_window()
