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

from playwright.sync_api import Browser, Page, sync_playwright
from playwright.sync_api import Error as PlaywrightError

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
import triggers as trigger_loader  # noqa: E402
import vscode  # noqa: E402


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


def _create_bait_files(filenames: list[str]) -> None:
    """Create empty bait files in the workspace for custom editor activation."""
    workspace = Path("/home/executor/workspace")
    for name in filenames:
        bait_path = workspace / name
        bait_path.parent.mkdir(parents=True, exist_ok=True)
        if not bait_path.exists():
            bait_path.write_text("")
            print(f"[+] Created bait file: {bait_path}")


def _run_extra_triggers(page: Page, payload: trigger_loader.TriggerPayload) -> None:
    """Run additional activation triggers beyond the standard scenarios."""
    from playwright.sync_api import Error as PlaywrightError

    # Open custom editor bait files
    for filename in payload.extra_custom_editor_files:
        try:
            print(f"[*] Opening custom editor bait file: {filename}")
            editor.open_file_by_name(page, filename)
            page.wait_for_timeout(2000)
            editor.close_active_editor(page)
            page.wait_for_timeout(500)
        except PlaywrightError as exc:
            print(f"[!] Custom editor trigger failed for {filename}: {exc}")

    # Trigger onUri via terminal xdg-open
    if payload.uri_trigger:
        try:
            print(f"[*] Triggering URI: {payload.uri_trigger}")
            terminal.new_terminal(page)
            page.wait_for_timeout(500)
            terminal.type_in_terminal(page, f"xdg-open '{payload.uri_trigger}'")
            page.wait_for_timeout(2000)
        except PlaywrightError as exc:
            print(f"[!] URI trigger failed: {exc}")

    # Trigger onTaskType via Command Palette
    if payload.run_task_trigger:
        try:
            print("[*] Running task trigger via Command Palette...")
            commands.run_command(page, "Tasks: Run Task")
            page.wait_for_timeout(1500)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except PlaywrightError as exc:
            print(f"[!] Task trigger failed: {exc}")

    # Trigger onWalkthrough via Command Palette
    if payload.run_walkthrough_trigger:
        try:
            print("[*] Running walkthrough trigger via Command Palette...")
            commands.run_command(page, "Welcome: Open Walkthrough")
            page.wait_for_timeout(2000)
            editor.close_active_editor(page)
            page.wait_for_timeout(500)
        except PlaywrightError as exc:
            print(f"[!] Walkthrough trigger failed: {exc}")

    # Trigger extension-specific commands via Command Palette
    if payload.extra_commands:
        print(f"[*] Invoking {len(payload.extra_commands)} extension commands...")
        for cmd_title in payload.extra_commands:
            try:
                print(f"[*] Running command: {cmd_title}")
                commands.run_command(page, cmd_title)
                page.wait_for_timeout(1500)
                # Dismiss any notifications/dialogs the command may trigger
                editor._dismiss_notification(page)
                page.wait_for_timeout(300)
            except PlaywrightError as exc:
                print(f"[!] Command '{cmd_title}' failed: {exc}")
                # Recover UI state so subsequent commands can run
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)


def _reload_window_under_monitoring(browser: Browser, page: Page) -> Page:
    """Reload the current VS Code window after monitoring has started."""
    print("[*] Reloading VS Code window under monitoring...")
    commands.run_command(page, "Developer: Reload Window")
    page.wait_for_timeout(3000)

    try:
        vscode.wait_until_ready(page, timeout_ms=30_000)
        print("[+] VS Code reloaded successfully")
        return page
    except PlaywrightError as exc:
        print(f"[!] Primary page lost during reload ({exc}), trying fallback...")

    contexts = browser.contexts
    if contexts and contexts[0].pages:
        reloaded_page = contexts[0].pages[0]
        vscode.wait_until_ready(reloaded_page, timeout_ms=30_000)
        print("[+] VS Code reloaded successfully (fallback)")
        return reloaded_page

    raise PlaywrightError("Unable to reconnect to VS Code window after reload")


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
    parser.add_argument(
        "--triggers",
        type=str,
        default=None,
        help="Path to trigger payload JSON (written by host-side scanner.triggers)",
    )
    parser.add_argument(
        "--reload-before-run",
        action="store_true",
        help="Reload the VS Code window after monitoring starts.",
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

        # Load trigger payload if provided
        trigger_payload: trigger_loader.TriggerPayload | None = None
        if args.triggers:
            print(f"[*] Loading trigger payload from {args.triggers}...")
            trigger_payload = trigger_loader.load_trigger_file(args.triggers)
            if trigger_payload:
                print(
                    f"[+] Trigger payload loaded: {len(trigger_payload.selected_scenarios)} scenarios"
                )
            else:
                print("[!] Trigger file not found or invalid, using defaults")

        # Create custom editor bait files in the workspace if needed
        if trigger_payload and trigger_payload.extra_custom_editor_files:
            _create_bait_files(trigger_payload.extra_custom_editor_files)

        mon = None
        try:
            if args.monitor:
                print("[*] Starting Extension Host monitoring...")
                mon = monitor.ExtensionMonitor(page)
                mon.start()

            if args.reload_before_run:
                page = _reload_window_under_monitoring(browser, page)
                if mon is not None:
                    mon.page = page

            executed_scenarios: list[str] = []

            if args.demo:
                run_demo(page)
                executed_scenarios.append("demo")
            elif args.scenario:
                print(f"[*] Running scenario: {args.scenario}")
                automation.run_scenario(page, args.scenario)
                executed_scenarios.append(args.scenario)
            elif trigger_payload and trigger_payload.selected_scenarios:
                print(
                    f"[*] Running selected scenarios: {trigger_payload.selected_scenarios}"
                )
                failed_scenarios = automation.run_selected_scenarios(
                    page, trigger_payload.selected_scenarios, shuffle=args.shuffle
                )
                executed_scenarios.extend(trigger_payload.selected_scenarios)
                if failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1
            else:
                print("[*] Running all automation scenarios...")
                failed_scenarios = automation.run_all_scenarios(
                    page, shuffle=args.shuffle
                )
                executed_scenarios.extend(automation.list_scenarios())
                if failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1

            # Run extra triggers from the payload
            if trigger_payload:
                _run_extra_triggers(page, trigger_payload)

            if mon is not None:
                print("[*] Collecting monitoring data...")
                mon.report.scenarios_run = executed_scenarios
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
