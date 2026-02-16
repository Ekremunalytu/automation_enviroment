"""Entrypoint for Playwright-based VS Code automation.

Run inside the executor container:
    python3 /home/executor/playwright/entrypoint.py              # run all scenarios
    python3 /home/executor/playwright/entrypoint.py --demo       # quick demo only
    python3 /home/executor/playwright/entrypoint.py --scenario coding_session
    python3 /home/executor/playwright/entrypoint.py --list       # list available scenarios
    python3 /home/executor/playwright/entrypoint.py --shuffle    # random scenario order
    python3 /home/executor/playwright/entrypoint.py --monitor    # run all + activation monitoring
    python3 /home/executor/playwright/entrypoint.py --monitor --scenario debug_session
"""

import argparse
import sys
from pathlib import Path

# Bootstrap: add parent dir so sibling imports don't conflict with pip `playwright`.
_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

import automation  # noqa: E402
import commands  # noqa: E402
import editor  # noqa: E402
import monitor  # noqa: E402
import panel  # noqa: E402
import sidebar  # noqa: E402
import terminal  # noqa: E402
import vscode  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402 — pip package


def run_demo(page: Page) -> None:
    """Quick demo exercising core helpers (legacy behavior)."""
    print("[*] Opening Explorer...")
    sidebar.open_explorer(page)
    page.wait_for_timeout(500)

    print("[*] Opening Extensions view...")
    sidebar.open_extensions_view(page)
    page.wait_for_timeout(500)

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

    print("[*] Opening terminal...")
    terminal.new_terminal(page)
    terminal.type_in_terminal(page, "echo 'hello from playwright'")
    page.wait_for_timeout(1000)

    print("[*] Opening Problems panel...")
    panel.open_problems(page)
    page.wait_for_timeout(500)

    print("[*] Running sample command...")
    commands.run_command(page, "Developer: Toggle Developer Tools")
    page.wait_for_timeout(1000)

    print("[*] Waiting 10 seconds - check via noVNC...")
    page.wait_for_timeout(10_000)


def main() -> None:
    parser = argparse.ArgumentParser(description="VS Code automation via Playwright")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="Run quick demo only")
    group.add_argument("--scenario", type=str, help="Run a single scenario by name")
    group.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument(
        "--shuffle", action="store_true", help="Randomize scenario order"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable Extension Host activation monitoring and generate report",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="/results/activation_report.json",
        help="Path for the monitoring report (default: /results/activation_report.json)",
    )
    args = parser.parse_args()

    if args.list:
        print("Available scenarios:")
        for name in automation.list_scenarios():
            print(f"  - {name}")
        return

    exit_code = 0

    with sync_playwright() as pw:
        print("[*] Connecting to VS Code...")
        browser, page = vscode.connect(pw)
        print(f"[+] Connected - page: {page.title()}")

        print("[*] Waiting for VS Code to be ready...")
        vscode.wait_until_ready(page)
        print("[+] VS Code is ready")

        mon = None
        try:
            if args.monitor:
                print("[*] Starting Extension Host monitoring...")
                mon = monitor.ExtensionMonitor(page)
                mon.start()

            if args.demo:
                run_demo(page)
            elif args.scenario:
                print(f"[*] Running scenario: {args.scenario}")
                automation.run_scenario(page, args.scenario)
            else:
                print("[*] Running all automation scenarios...")
                failed_scenarios = automation.run_all_scenarios(
                    page, shuffle=args.shuffle
                )
                if failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1

            if mon is not None:
                print("[*] Collecting monitoring data...")
                report = mon.stop()
                report.print_summary()
                report.save(args.report_path)
        finally:
            vscode.disconnect(browser)
            print("[+] Completed")

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
