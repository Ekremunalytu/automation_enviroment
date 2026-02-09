"""Demo entrypoint showing Playwright UI helper usage.

Run inside the executor container:
    python3 /home/executor/playwright/entrypoint.py
"""

import sys
from pathlib import Path

# Bootstrap: add parent dir so `import playwright_helpers` style won't conflict
# with the pip `playwright` package. We import siblings via their module names.
_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import commands  # noqa: E402
import editor  # noqa: E402
import panel  # noqa: E402
import sidebar  # noqa: E402
import terminal  # noqa: E402
import vscode  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402 — pip package


def main() -> None:
    with sync_playwright() as pw:
        # --- Connect ---
        print("[*] Connecting to VS Code...")
        browser, page = vscode.connect(pw)
        print(f"[+] Connected - page: {page.title()}")

        print("[*] Waiting for VS Code to be ready...")
        vscode.wait_until_ready(page)
        print("[+] VS Code is ready")

        # --- Sidebar demo ---
        print("[*] Opening Explorer...")
        sidebar.open_explorer(page)
        page.wait_for_timeout(500)

        print("[*] Opening Extensions view...")
        sidebar.open_extensions_view(page)
        page.wait_for_timeout(500)

        # --- Editor demo ---
        print("[*] Creating new file...")
        editor.new_untitled_file(page)
        editor.type_in_editor(page, "# Playwright demo")
        page.wait_for_timeout(300)

        print("[*] Saving file...")
        editor.save_file_as(page, "demo.py")
        page.wait_for_timeout(500)

        print("[*] Opening hello.py...")
        editor.open_file_by_name(page, "hello.py")
        page.wait_for_timeout(500)

        # --- Terminal demo ---
        print("[*] Opening terminal...")
        terminal.new_terminal(page)
        terminal.type_in_terminal(page, "echo 'hello from playwright'")
        page.wait_for_timeout(1000)

        # --- Panel demo ---
        print("[*] Opening Problems panel...")
        panel.open_problems(page)
        page.wait_for_timeout(500)

        # --- Command demo ---
        print("[*] Running sample command...")
        commands.run_command(page, "Developer: Toggle Developer Tools")
        page.wait_for_timeout(1000)

        # --- Wait for observation ---
        print("[*] Waiting 10 seconds - check via noVNC...")
        page.wait_for_timeout(10_000)

        # --- Disconnect ---
        vscode.disconnect(browser)
        print("[+] Completed")


if __name__ == "__main__":
    main()
