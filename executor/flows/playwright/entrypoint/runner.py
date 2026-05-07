"""Runtime flow helpers for the Playwright executor entrypoint."""

from __future__ import annotations

from uuid import uuid4

from playwright.sync_api import Error as PlaywrightError

from ..wait_helpers import wait_for_idle_observation
from .cli import build_parser
from .triggers import (
    reload_window_under_monitoring,
    resolve_execution_plan,
    run_extra_triggers,
)


def run_demo(page, *, deps) -> None:
    """Quick demo exercising core helpers (legacy behavior)."""
    print("[*] Opening Explorer...")
    deps.sidebar.open_explorer(page)
    page.wait_for_timeout(500)
    print("[*] Opening Extensions view...")
    deps.sidebar.open_extensions_view(page)
    page.wait_for_timeout(500)
    print("[*] Creating new file...")
    deps.editor.new_untitled_file(page)
    deps.editor.type_in_editor(page, "# Playwright demo")
    page.wait_for_timeout(300)
    print("[*] Saving file...")
    deps.editor.save_file_as(page, "demo.py")
    page.wait_for_timeout(500)
    print("[*] Opening hello.py...")
    deps.editor.open_file_by_name(page, "hello.py")
    page.wait_for_timeout(500)
    print("[*] Opening terminal...")
    deps.terminal.new_terminal(page)
    deps.terminal.type_in_terminal(page, "echo 'hello from playwright'")
    page.wait_for_timeout(1000)
    print("[*] Opening Problems panel...")
    deps.panel.open_problems(page)
    page.wait_for_timeout(500)
    print("[*] Running sample command...")
    deps.commands.run_command(page, "Developer: Toggle Developer Tools")
    page.wait_for_timeout(1000)
    print("[*] Waiting 10 seconds - check via noVNC...")
    page.wait_for_timeout(10_000)


def create_bait_files(filenames: list[str], *, deps) -> list[str]:
    """Create empty bait files in the workspace for custom editor activation."""
    created: list[str] = []
    for bait_path in deps.workspace.create_bait_files(filenames):
        print(f"[+] Created bait file: {bait_path}")
        created.append(str(bait_path))
    return created


def default_report_path() -> str:
    return f"/results/activation_report_{uuid4().hex}.json"


def _default_report_path_for_deps(deps) -> str:
    override = getattr(deps, "_default_report_path", None)
    if callable(override):
        return str(override())
    return default_report_path()


def _create_bait_files_for_deps(filenames: list[str], *, deps) -> list[str]:
    override = getattr(deps, "_create_bait_files", None)
    if callable(override):
        return list(override(filenames))
    return create_bait_files(filenames, deps=deps)


def _resolve_execution_plan_for_deps(
    skip_automation: bool,
    scenario: str | None,
    trigger_payload,
    *,
    deps,
) -> tuple[str, list[str]]:
    override = getattr(deps, "_resolve_execution_plan", None)
    if callable(override):
        return override(skip_automation, scenario, trigger_payload)
    return resolve_execution_plan(skip_automation, scenario, trigger_payload)


def _run_demo_for_deps(page, *, deps) -> None:
    override = getattr(deps, "run_demo", None)
    if callable(override) and override is not run_demo:
        override(page)
        return
    run_demo(page, deps=deps)


def _reload_window_under_monitoring_for_deps(browser, page, *, deps):
    override = getattr(deps, "_reload_window_under_monitoring", None)
    if callable(override):
        return override(browser, page)
    return reload_window_under_monitoring(browser, page, deps=deps)


def _run_extra_triggers_for_deps(
    page,
    trigger_payload,
    *,
    deps,
    automation_event_recorder=None,
    verification_monitor=None,
) -> list[str]:
    override = getattr(deps, "_run_extra_triggers", None)
    if callable(override):
        return list(
            override(
                page,
                trigger_payload,
                automation_event_recorder=automation_event_recorder,
                verification_monitor=verification_monitor,
            )
        )
    return run_extra_triggers(
        page,
        trigger_payload,
        deps=deps,
        automation_event_recorder=automation_event_recorder,
        verification_monitor=verification_monitor,
    )


def _empty_execution_result(*, deps, requested_scenarios: list[str] | None = None):
    return deps.stimulus.AutomationExecutionResult(
        requested_scenarios=list(requested_scenarios or [])
    )


def _normalize_execution_result(outcome, *, deps, requested_scenarios: list[str]):
    if isinstance(outcome, list):
        result = _empty_execution_result(
            deps=deps,
            requested_scenarios=requested_scenarios,
        )
        result.failed_scenarios = [
            str(name).strip() for name in outcome if str(name).strip()
        ]
        result.executed_scenarios = list(requested_scenarios)
        return result

    if outcome is None:
        return _empty_execution_result(
            deps=deps,
            requested_scenarios=requested_scenarios,
        )

    if not hasattr(outcome, "requested_scenarios") or not getattr(
        outcome, "requested_scenarios", None
    ):
        outcome.requested_scenarios = list(requested_scenarios)
    if not hasattr(outcome, "executed_scenarios"):
        outcome.executed_scenarios = []
    if not hasattr(outcome, "failed_scenarios"):
        outcome.failed_scenarios = []
    if not hasattr(outcome, "skipped_scenarios"):
        outcome.skipped_scenarios = []
    if not hasattr(outcome, "extra_trigger_failures"):
        outcome.extra_trigger_failures = []
    return outcome


def main(*, deps) -> None:
    args = build_parser(
        default_report_path=_default_report_path_for_deps(deps)
    ).parse_args()
    if args.list:
        print("Available scenarios:")
        for name in deps.automation.list_scenarios():
            print(f"  - {name}")
        return

    exit_code = 0
    with deps.sync_playwright() as pw:
        print("[*] Connecting to VS Code...")
        browser, page = deps.vscode.connect(pw)
        print(f"[+] Connected - page: {page.title()}")
        print("[*] Waiting for VS Code to be ready...")
        deps.vscode.wait_until_ready(page)
        print("[+] VS Code is ready")

        trigger_payload = None
        trigger_plan_requested = bool(args.triggers)
        if args.triggers:
            print(f"[*] Loading trigger payload from {args.triggers}...")
            trigger_payload = deps.trigger_loader.load_trigger_file(args.triggers)
            if trigger_payload:
                print(
                    f"[+] Trigger payload loaded: {len(trigger_payload.selected_scenarios)} scenarios"
                )
            else:
                print("[!] Trigger file not found or invalid, using defaults")

        bait_files_created: list[str] = []
        if trigger_payload and trigger_payload.extra_custom_editor_files:
            bait_files_created = _create_bait_files_for_deps(
                trigger_payload.extra_custom_editor_files,
                deps=deps,
            )

        mon = None
        try:
            if args.monitor:
                print("[*] Starting Extension Host monitoring...")
                mon = deps.monitor.ExtensionMonitor(
                    page,
                    report_path=args.report_path,
                    target_extension_id=args.target_extension_id,
                )
                mon.start()
                deps.automation.set_scenario_event_reporter(mon.record_scenario_event)
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
                        "Trigger payload could not be loaded inside the executor.",
                        status="failed",
                    )
                if bait_files_created:
                    mon.record_automation_event(
                        "trigger_bait_files",
                        "Created bait files for trigger coverage: "
                        + ", ".join(bait_files_created),
                        status="completed",
                    )

            if args.reload_before_run:
                page = _reload_window_under_monitoring_for_deps(
                    browser, page, deps=deps
                )
                if mon is not None:
                    mon.page = page

            if mon is not None:
                mon.attach_runtime_tracers()

            def _on_page_reloaded(reloaded_page) -> None:
                nonlocal page
                page = reloaded_page
                if mon is not None:
                    mon.page = reloaded_page

            def _probe_ui_blocker(current_page, scenario_name: str) -> None:
                if mon is None:
                    return
                try:
                    text = deps.editor._dismiss_notification(current_page)
                except (PlaywrightError, RuntimeError, ValueError):
                    return
                if not text:
                    return
                mon.record_automation_event(
                    "ui_blocker_detected",
                    f"Detected UI blocker before scenario {scenario_name!r}: {text}",
                    status="running",
                    scenario_name=scenario_name,
                )
                mon.record_automation_event(
                    "ui_blocker_dismissed",
                    f"Dismissed UI blocker before scenario {scenario_name!r}: {text}",
                    status="completed",
                    scenario_name=scenario_name,
                )

            execution_mode, planned_scenarios = _resolve_execution_plan_for_deps(
                args.skip_automation,
                args.scenario,
                trigger_payload,
                deps=deps,
            )
            execution_result = _empty_execution_result(
                deps=deps, requested_scenarios=planned_scenarios
            )
            if mon is not None:
                mon.set_trigger_execution_mode(execution_mode)
                mon.record_automation_event(
                    "trigger_execution_mode",
                    "Resolved trigger execution mode: "
                    + execution_mode
                    + (
                        f" ({', '.join(planned_scenarios)})"
                        if planned_scenarios
                        else ""
                    ),
                    status="completed",
                )

            if args.demo:
                _run_demo_for_deps(page, deps=deps)
                execution_result = _empty_execution_result(
                    deps=deps, requested_scenarios=["demo"]
                )
                execution_result.executed_scenarios = ["demo"]
            elif execution_mode == "skip_automation":
                print("[*] Skipping automation scenario execution by request...")
            elif execution_mode == "layered_passes":
                print("[*] Running layered stimulus plan...")
                execution_result = _normalize_execution_result(
                    deps.stimulus.run_stimulus_plan(page, trigger_payload, monitor=mon),
                    deps=deps,
                    requested_scenarios=planned_scenarios,
                )
                if mon is not None and trigger_payload is not None:
                    mon.mark_trigger_plan_applied(
                        scenarios=execution_result.requested_scenarios,
                        trigger_path=args.triggers,
                    )
                    mon.record_automation_event(
                        "trigger_plan_applied",
                        "Trigger plan applied as layered passes with "
                        f"{len(trigger_payload.event_attempts)} event target(s).",
                        status="completed",
                    )
                if execution_result.extra_trigger_failures:
                    print("[!] Layered extra trigger failures:")
                    for item in execution_result.extra_trigger_failures:
                        print(f"  - {item}")
                    exit_code = 1
                if mon is not None:
                    wait_for_idle_observation(
                        page,
                        monitor=mon,
                        event_recorder=mon.record_automation_event,
                    )
            elif execution_mode == "selected_scenarios":
                print(f"[*] Running selected scenarios: {planned_scenarios}")
                execution_result = _normalize_execution_result(
                    deps.automation.run_selected_scenarios(
                        page,
                        planned_scenarios,
                        shuffle=args.shuffle,
                        retry_on_crash=args.retry_on_crash,
                        browser=browser,
                        on_page_reloaded=_on_page_reloaded,
                        ui_blocker_probe=_probe_ui_blocker,
                    ),
                    deps=deps,
                    requested_scenarios=planned_scenarios,
                )
                if mon is not None:
                    mon.mark_trigger_plan_applied(
                        scenarios=execution_result.requested_scenarios,
                        trigger_path=args.triggers,
                    )
                    mon.record_automation_event(
                        "trigger_plan_applied",
                        "Trigger plan selected scenarios for execution: "
                        + ", ".join(execution_result.requested_scenarios),
                        status="completed",
                    )
                if execution_result.failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in execution_result.failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1
                if mon is not None:
                    wait_for_idle_observation(
                        page,
                        monitor=mon,
                        event_recorder=mon.record_automation_event,
                    )
            elif execution_mode == "single_scenario":
                scenario_name = planned_scenarios[0]
                print(f"[*] Running scenario: {scenario_name}")
                execution_result = _normalize_execution_result(
                    deps.automation.run_selected_scenarios(
                        page,
                        [scenario_name],
                        shuffle=False,
                        retry_on_crash=args.retry_on_crash,
                        browser=browser,
                        on_page_reloaded=_on_page_reloaded,
                        ui_blocker_probe=_probe_ui_blocker,
                    ),
                    deps=deps,
                    requested_scenarios=[scenario_name],
                )
                if execution_result.failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in execution_result.failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1
                elif execution_result.skipped_scenarios:
                    print("[!] Skipped scenarios:")
                    for item in execution_result.skipped_scenarios:
                        print(f"  - {item.name}: {item.reason_code}")
                    exit_code = 1
            else:
                print("[*] Running all automation scenarios...")
                execution_result = _normalize_execution_result(
                    deps.automation.run_all_scenarios(
                        page,
                        shuffle=args.shuffle,
                        retry_on_crash=args.retry_on_crash,
                        browser=browser,
                        on_page_reloaded=_on_page_reloaded,
                        ui_blocker_probe=_probe_ui_blocker,
                    ),
                    deps=deps,
                    requested_scenarios=deps.automation.list_scenarios(),
                )
                if execution_result.failed_scenarios:
                    print("[!] Failed scenarios:")
                    for name in execution_result.failed_scenarios:
                        print(f"  - {name}")
                    exit_code = 1

            if trigger_payload and not trigger_payload.stimulus_passes:
                if mon is not None and not mon.report.trigger_plan_applied:
                    mon.mark_trigger_plan_applied(
                        scenarios=execution_result.requested_scenarios
                        or trigger_payload.selected_scenarios,
                        trigger_path=args.triggers,
                    )
                    mon.record_automation_event(
                        "trigger_plan_applied",
                        "Trigger plan was applied through executor-side payload actions.",
                        status="completed",
                    )
                execution_result.extra_trigger_failures = _run_extra_triggers_for_deps(
                    page,
                    trigger_payload,
                    deps=deps,
                    automation_event_recorder=(
                        mon.record_automation_event if mon is not None else None
                    ),
                    verification_monitor=mon,
                )
                if execution_result.extra_trigger_failures:
                    print("[!] Extra trigger failures:")
                    for item in execution_result.extra_trigger_failures:
                        print(f"  - {item}")
                    exit_code = 1

            if (
                execution_mode in {"selected_scenarios", "single_scenario"}
                and execution_result.skipped_scenarios
                and not execution_result.executed_scenarios
            ):
                print("[!] Skipped scenarios:")
                for item in execution_result.skipped_scenarios:
                    print(f"  - {item.name}: {item.reason_code}")
                exit_code = 1

            if mon is not None:
                print("[*] Collecting monitoring data...")
                if hasattr(mon, "record_execution_result"):
                    mon.record_execution_result(execution_result)
                else:
                    mon.report.requested_scenarios = list(
                        execution_result.requested_scenarios
                    )
                    mon.report.extra_trigger_failures = list(
                        execution_result.extra_trigger_failures
                    )
                    mon.record_failed_scenarios(execution_result.failed_scenarios)
                    mon.report.scenarios_run = list(execution_result.executed_scenarios)
                report = mon.stop()
                # W11-3: surface the runner outcome on the report before
                # the final disk write so analysts can correlate the saved
                # `runner_exit_code` / `runner_status` with the run that
                # produced the activation evidence. exit_code is finalized
                # by this point — every code path that mutates it lives
                # above the `if mon is not None` block.
                mon.set_runner_status(exit_code)
                report.print_summary()
                report.save(args.report_path)
        finally:
            deps.automation.set_scenario_event_reporter(None)
            deps.vscode.disconnect(browser)
            print("[+] Completed")

    if exit_code:
        raise SystemExit(exit_code)
