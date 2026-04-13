"""Entrypoint for Playwright-based VS Code automation.

Run inside the executor container:
    python3 /home/executor/flows/playwright/entrypoint.py              # run all scenarios
    python3 /home/executor/flows/playwright/entrypoint.py --demo       # quick demo only
    python3 /home/executor/flows/playwright/entrypoint.py --scenario coding_session
    python3 /home/executor/flows/playwright/entrypoint.py --list       # list available scenarios
    python3 /home/executor/flows/playwright/entrypoint.py --shuffle    # random scenario order
    python3 /home/executor/flows/playwright/entrypoint.py --monitor    # run all + activation monitoring
    python3 /home/executor/flows/playwright/entrypoint.py --monitor --scenario debug_session
"""

import argparse
import sys
from collections.abc import Callable
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
import workspace  # noqa: E402


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


def _create_bait_files(filenames: list[str]) -> list[str]:
    """Create empty bait files in the workspace for custom editor activation."""
    created: list[str] = []
    for bait_path in workspace.create_bait_files(filenames):
        print(f"[+] Created bait file: {bait_path}")
        created.append(str(bait_path))
    return created


def _resolve_execution_plan(
    scenario: str | None,
    trigger_payload: trigger_loader.TriggerPayload | None,
) -> tuple[str, list[str]]:
    """Pick selected trigger scenarios first, then explicit fallback, else run all."""
    if trigger_payload and trigger_payload.selected_scenarios:
        return "selected", list(trigger_payload.selected_scenarios)
    if scenario:
        return "single", [scenario]
    return "all", []


def _run_extra_triggers(
    page: Page,
    payload: trigger_loader.TriggerPayload,
    automation_event_recorder: Callable[[str, str, str, str, str], None] | None = None,
    verification_monitor: monitor.ExtensionMonitor | None = None,
) -> list[str]:
    """Run additional activation triggers beyond the standard scenarios."""
    from playwright.sync_api import Error as PlaywrightError

    failed_triggers: list[str] = []

    def emit(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        if automation_event_recorder is None:
            return
        automation_event_recorder(
            kind,
            message,
            status,
            scenario_name,
            activation_event,
        )

    def dismiss_ui_blocker(context: str, activation_event: str) -> bool:
        blocker_text = editor._dismiss_notification(page)
        if not blocker_text:
            return False
        emit(
            "ui_blocker_detected",
            f"Detected UI blocker during {context}: {blocker_text}",
            "running",
            activation_event=activation_event,
        )
        emit(
            "ui_blocker_dismissed",
            f"Dismissed UI blocker during {context}: {blocker_text}",
            "completed",
            activation_event=activation_event,
        )
        return True

    # Open custom editor bait files
    for filename in payload.extra_custom_editor_files:
        emit(
            "extra_trigger",
            f"Opening custom editor bait file {filename}",
            "running",
            activation_event="onCustomEditor",
        )
        try:
            print(f"[*] Opening custom editor bait file: {filename}")
            editor.open_file_by_name(page, filename)
            page.wait_for_timeout(2000)
            editor.close_active_editor(page)
            page.wait_for_timeout(500)
            emit(
                "extra_trigger",
                f"Opened custom editor bait file {filename}",
                "completed",
                activation_event="onCustomEditor",
            )
        except PlaywrightError as exc:
            print(f"[!] Custom editor trigger failed for {filename}: {exc}")
            emit(
                "extra_trigger",
                f"Custom editor trigger failed for {filename}: {exc}",
                "failed",
                activation_event="onCustomEditor",
            )
            failed_triggers.append(f"custom_editor:{filename}")

    # Trigger onUri via terminal xdg-open
    if payload.uri_trigger:
        emit(
            "extra_trigger",
            f"Triggering URI {payload.uri_trigger}",
            "running",
            activation_event="onUri",
        )
        try:
            print(f"[*] Triggering URI: {payload.uri_trigger}")
            terminal.new_terminal(page)
            page.wait_for_timeout(500)
            terminal.type_in_terminal(page, f"xdg-open '{payload.uri_trigger}'")
            page.wait_for_timeout(2000)
            emit(
                "extra_trigger",
                f"Triggered URI {payload.uri_trigger}",
                "completed",
                activation_event="onUri",
            )
        except PlaywrightError as exc:
            print(f"[!] URI trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"URI trigger failed: {exc}",
                "failed",
                activation_event="onUri",
            )
            failed_triggers.append("uri_trigger")

    # Trigger onTaskType via Command Palette
    if payload.run_task_trigger:
        emit(
            "extra_trigger",
            "Running task trigger via Command Palette",
            "running",
            activation_event="onTaskType",
        )
        try:
            print("[*] Running task trigger via Command Palette...")
            commands.run_command(page, "Tasks: Run Task")
            page.wait_for_timeout(1500)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            emit(
                "extra_trigger",
                "Completed task trigger via Command Palette",
                "completed",
                activation_event="onTaskType",
            )
        except PlaywrightError as exc:
            print(f"[!] Task trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"Task trigger failed: {exc}",
                "failed",
                activation_event="onTaskType",
            )
            failed_triggers.append("task_trigger")

    # Trigger onWalkthrough via Command Palette
    if payload.run_walkthrough_trigger:
        emit(
            "extra_trigger",
            "Opening walkthrough via Command Palette",
            "running",
            activation_event="onWalkthrough",
        )
        try:
            print("[*] Running walkthrough trigger via Command Palette...")
            commands.run_command(page, "Welcome: Open Walkthrough")
            page.wait_for_timeout(2000)
            editor.close_active_editor(page)
            page.wait_for_timeout(500)
            emit(
                "extra_trigger",
                "Completed walkthrough trigger via Command Palette",
                "completed",
                activation_event="onWalkthrough",
            )
        except PlaywrightError as exc:
            print(f"[!] Walkthrough trigger failed: {exc}")
            emit(
                "extra_trigger",
                f"Walkthrough trigger failed: {exc}",
                "failed",
                activation_event="onWalkthrough",
            )
            failed_triggers.append("walkthrough_trigger")

    # Trigger extension-specific commands via Command Palette
    if payload.extra_commands:
        print(f"[*] Invoking {len(payload.extra_commands)} extension commands...")
        for cmd_title in payload.extra_commands:
            emit(
                "command",
                f"Running command {cmd_title}",
                "running",
                activation_event="onCommand",
            )
            try:
                print(f"[*] Running command: {cmd_title}")
                baseline = (
                    verification_monitor.capture_runtime_snapshot()
                    if verification_monitor is not None
                    else None
                )
                commands.run_command(page, cmd_title)
                page.wait_for_timeout(1500)
                dismiss_ui_blocker(f"command {cmd_title}", "onCommand")
                page.wait_for_timeout(300)
                if verification_monitor is not None and baseline is not None:
                    verification_monitor.verify_target_reaction(
                        baseline,
                        capability="commands",
                        trigger_label=cmd_title,
                        activation_event="onCommand",
                    )
                emit(
                    "command",
                    f"Completed command {cmd_title}",
                    "completed",
                    activation_event="onCommand",
                )
            except PlaywrightError as exc:
                print(f"[!] Command '{cmd_title}' failed: {exc}")
                # Recover UI state so subsequent commands can run
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                emit(
                    "ui_blocker_unresolved",
                    f"Command {cmd_title} left the UI in a blocked state: {exc}",
                    "failed",
                    activation_event="onCommand",
                )
                emit(
                    "command",
                    f"Command {cmd_title} failed: {exc}",
                    "failed",
                    activation_event="onCommand",
                )
                failed_triggers.append(f"command:{cmd_title}")

    return failed_triggers


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
    parser.add_argument(
        "--target-extension-id",
        type=str,
        default="",
        help="Publisher.name identifier for the extension under analysis.",
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
        trigger_plan_requested = bool(args.triggers)
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
        bait_files_created: list[str] = []
        if trigger_payload and trigger_payload.extra_custom_editor_files:
            bait_files_created = _create_bait_files(
                trigger_payload.extra_custom_editor_files
            )

        mon = None
        try:
            if args.monitor:
                print("[*] Starting Extension Host monitoring...")
                mon = monitor.ExtensionMonitor(
                    page,
                    report_path=args.report_path,
                    target_extension_id=args.target_extension_id,
                )
                mon.start()
                automation.set_scenario_event_reporter(mon.record_scenario_event)
                mon.report.trigger_plan_requested = trigger_plan_requested
                mon.report.trigger_plan_path = args.triggers or ""
                if trigger_payload is not None:
                    mon.apply_trigger_payload(trigger_payload)
                    mon.record_automation_event(
                        "trigger_plan_loaded",
                        (
                            "Trigger payload loaded inside the executor: "
                            f"{len(trigger_payload.selected_scenarios)} selected scenario(s)."
                        ),
                        status="completed",
                    )
                elif trigger_plan_requested:
                    mon.mark_trigger_plan_missing(args.triggers or "")
                    mon.record_automation_event(
                        "trigger_plan_missing",
                        (
                            "Trigger payload could not be loaded inside the executor; "
                            "continuing with degraded reliability."
                        ),
                        status="failed",
                    )
                if bait_files_created:
                    mon.record_automation_event(
                        "trigger_bait_files",
                        (
                            "Created bait files for trigger coverage: "
                            + ", ".join(bait_files_created)
                        ),
                        status="completed",
                    )

            if args.reload_before_run:
                page = _reload_window_under_monitoring(browser, page)
                if mon is not None:
                    mon.page = page

            if mon is not None:
                mon.attach_runtime_tracers()

            executed_scenarios: list[str] = []
            failed_scenarios: list[str] = []
            execution_plan, planned_scenarios = _resolve_execution_plan(
                args.scenario,
                trigger_payload,
            )

            if args.demo:
                run_demo(page)
                executed_scenarios.append("demo")
            elif execution_plan == "selected":
                print(f"[*] Running selected scenarios: {planned_scenarios}")
                failed_scenarios = automation.run_selected_scenarios(
                    page,
                    planned_scenarios,
                    shuffle=args.shuffle,
                )
                executed_scenarios.extend(planned_scenarios)
                if mon is not None:
                    mon.mark_trigger_plan_applied(
                        scenarios=planned_scenarios,
                        trigger_path=args.triggers,
                    )
                    mon.record_automation_event(
                        "trigger_plan_applied",
                        (
                            "Trigger plan selected scenarios for execution: "
                            + ", ".join(planned_scenarios)
                        ),
                        status="completed",
                    )
                if failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1
            elif execution_plan == "single":
                scenario_name = planned_scenarios[0]
                print(f"[*] Running scenario: {scenario_name}")
                automation.run_scenario(page, scenario_name)
                executed_scenarios.append(scenario_name)
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
            extra_trigger_failures: list[str] = []
            if trigger_payload:
                if mon is not None and not mon.report.trigger_plan_applied:
                    mon.mark_trigger_plan_applied(
                        scenarios=trigger_payload.selected_scenarios,
                        trigger_path=args.triggers,
                    )
                    mon.record_automation_event(
                        "trigger_plan_applied",
                        "Trigger plan was applied through executor-side payload actions.",
                        status="completed",
                    )
                extra_trigger_failures = _run_extra_triggers(
                    page,
                    trigger_payload,
                    automation_event_recorder=(
                        mon.record_automation_event if mon is not None else None
                    ),
                    verification_monitor=mon,
                )

            if mon is not None:
                print("[*] Collecting monitoring data...")
                mon.report.scenarios_run = executed_scenarios
                mon.record_failed_scenarios(failed_scenarios)
                mon.report.extra_trigger_failures = extra_trigger_failures
                report = mon.stop()
                report.print_summary()
                report.save(args.report_path)
        finally:
            automation.set_scenario_event_reporter(None)
            vscode.disconnect(browser)
            print("[+] Completed")

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
