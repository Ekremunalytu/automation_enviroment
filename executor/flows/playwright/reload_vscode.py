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

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from . import vscode

_RELOAD_TIMEOUT_MS = vscode.DEFAULT_RECONNECT_TIMEOUT_MS
"""Maximum time (ms) to wait for workbench to become ready after reload."""


def reload_window() -> None:
    """Connect to VS Code via CDP, reload the window, wait until ready.

    The per-launch HMAC secret rewrite is handled inside
    ``vscode.reload_workbench_window`` so every reload seam in the analyze
    loop receives the fresh secret, not just this standalone entry point.
    """
    browser = None
    with sync_playwright() as pw:
        try:
            browser, page = vscode.connect_to_ready_workbench(
                pw,
                timeout_ms=_RELOAD_TIMEOUT_MS,
                log=print,
            )
            vscode.reload_workbench_window(
                browser,
                page,
                reconnect_timeout_ms=_RELOAD_TIMEOUT_MS,
                log=print,
            )
        finally:
            if browser is not None:
                try:
                    vscode.disconnect(browser)
                except PlaywrightError:
                    print(
                        "[reload] disconnect: Failed to close the CDP browser cleanly.",
                        file=sys.stderr,
                    )


def main() -> int:
    try:
        reload_window()
    except vscode.ReloadWindowError as exc:
        print(f"[reload] ERROR {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
