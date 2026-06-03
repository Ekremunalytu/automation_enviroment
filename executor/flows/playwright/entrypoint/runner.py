"""Runtime flow helpers for the Playwright executor entrypoint."""

from __future__ import annotations

from uuid import uuid4

from .cli import build_parser
from .dispatch import (
    PageRef,
    apply_extra_triggers_if_needed,
    dispatch_execution,
    finalize_monitor_report,
    setup_monitor,
    summarize_skipped_scenarios_if_needed,
)
from .triggers import reload_window_under_monitoring, resolve_execution_plan


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


def _reload_window_under_monitoring_for_deps(browser, page, *, deps):
    override = getattr(deps, "_reload_window_under_monitoring", None)
    if callable(override):
        return override(browser, page)
    return reload_window_under_monitoring(browser, page, deps=deps)


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
    mon = None
    execution_result = None
    with deps.sync_playwright() as pw:
        print("[*] Connecting to VS Code...")
        browser, page = deps.vscode.connect(pw)
        print(f"[+] Connected - page: {page.title()}")
        print("[*] Waiting for VS Code to be ready...")
        deps.vscode.wait_until_ready(page)
        print("[+] VS Code is ready")

        trigger_payload = None
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

        try:
            mon = setup_monitor(
                page, args, trigger_payload, bait_files_created, deps=deps
            )

            if args.reload_before_run:
                page = _reload_window_under_monitoring_for_deps(
                    browser, page, deps=deps
                )
                if mon is not None:
                    mon.page = page

            if mon is not None:
                mon.attach_runtime_tracers()

            page_ref = PageRef(page)

            execution_mode, planned_scenarios = _resolve_execution_plan_for_deps(
                args.skip_automation,
                args.scenario,
                trigger_payload,
                deps=deps,
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

            execution_result, dispatch_exit = dispatch_execution(
                page_ref,
                browser,
                args,
                mon,
                trigger_payload,
                planned_scenarios,
                execution_mode,
                deps=deps,
            )
            exit_code |= dispatch_exit
            exit_code |= apply_extra_triggers_if_needed(
                page_ref, args, mon, trigger_payload, execution_result, deps=deps
            )
            exit_code |= summarize_skipped_scenarios_if_needed(
                execution_mode, execution_result
            )
        finally:
            # W22: finalize in ``finally`` so the Extension Host activation
            # parse + ``report.save`` ALWAYS run — even if the stimulus/extra-
            # trigger phase raised on a degraded renderer or a SIGTERM unwinds
            # the stack here. Without this the report was left as the last live
            # persist with ``activated: []`` (target "never observed") although
            # the activation was sitting in exthost.log. ``finalize_monitor_report``
            # is idempotent + tolerates ``execution_result is None``.
            finalize_monitor_report(mon, execution_result, exit_code, args)
            deps.automation.set_scenario_event_reporter(None)
            deps.vscode.disconnect(browser)
            print("[+] Completed")

    if exit_code:
        raise SystemExit(exit_code)
