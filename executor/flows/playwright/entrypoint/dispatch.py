"""Execution dispatch helpers for the Playwright entrypoint runner.

Extracted from `runner.py::main` (W12-4) so the runner module stays under
the ≤200 LoC readability budget. Each helper here is pure relocation of
prior `main()` logic; behavior, ordering, and the ``*, deps``-injection
convention used everywhere else in the entrypoint package are preserved.
"""

from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError

from ..health.reconciliation import load_harness_python_secret
from ..wait_helpers import wait_for_idle_observation
from .triggers import run_extra_triggers


class PageRef:
    """Mutable reference to the active Playwright page.

    The retry-on-crash callback rebinds the live page after a window
    reload; siblings (UI blocker probe, dispatch helpers, monitor) need
    that rebind to be visible without using ``nonlocal`` across module
    boundaries.
    """

    __slots__ = ("value",)

    def __init__(self, page) -> None:
        self.value = page


def _run_demo_for_deps(page, *, deps) -> None:
    # Lazy import: dispatch.py is loaded during runner.py's import; a
    # top-level `from .runner import run_demo` would re-enter the
    # partially-loaded runner module.
    from .runner import run_demo as _runner_run_demo

    override = getattr(deps, "run_demo", None)
    if callable(override) and override is not _runner_run_demo:
        override(page)
        return
    _runner_run_demo(page, deps=deps)


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
        # W16-1: stimulus dispatch collapsed (run_stimulus_plan /
        # run_selected_scenarios / run_all_scenarios returned None) and
        # every requested scenario is about to silently vanish. Emit a
        # specific ``dispatch_outcome_none`` reason for each one so the
        # downstream ``ScenarioAccountant._validate_scenario_conservation``
        # last-mile guard no longer has to fall back to the generic
        # ``unaccounted_dropout`` label. This is the upstream emit-site
        # fix for the W14-1 carry-over bug class observed deterministically
        # in production on 2026-05-14 + 2026-05-15.
        result = _empty_execution_result(
            deps=deps,
            requested_scenarios=requested_scenarios,
        )
        result.skipped_scenarios = [
            deps.stimulus.SkippedScenarioRecord(
                name=str(name).strip(),
                reason_code="dispatch_outcome_none",
                detail=(
                    "Stimulus dispatcher returned None; every requested "
                    "scenario silently dropped at the dispatch normalizer."
                ),
            )
            for name in requested_scenarios
            if str(name).strip()
        ]
        return result

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


def setup_monitor(page, args, trigger_payload, bait_files_created, *, deps):
    """Initialize ExtensionMonitor when ``--monitor`` enabled. None otherwise."""
    if not args.monitor:
        return None
    print("[*] Starting Extension Host monitoring...")
    mon = deps.monitor.ExtensionMonitor(
        page,
        report_path=args.report_path,
        target_extension_id=args.target_extension_id,
    )
    # W13-1 (Codex H6): consume the per-launch HMAC secret
    # ``launch_vscode.sh`` wrote (and unlink it) before the analyzed
    # target VSIX has any chance to read /results. The value is held
    # only in this process's memory via the report field; reconciliation
    # uses it to authenticate harness completion markers. Empty value
    # (file missing or unreadable) keeps reconciliation in fail-closed
    # mode — no harness attempt is verified by trace alone.
    mon.report.expected_harness_nonce = load_harness_python_secret()
    # W13-12 (Codex F2 close-pass): production paths must fail-closed
    # when the eager-consumed secret is unavailable. Empty
    # expected_harness_nonce above + this flag → reconciliation refuses
    # to count harness completion traces by phase alone (target
    # extensions can forge that line). Test fixtures that construct
    # ActivationReport directly keep the default False so the pre-W13-1
    # phase-only regression surface stays GREEN.
    mon.report.harness_handshake_required = True
    mon.start()
    deps.automation.set_scenario_event_reporter(mon.record_scenario_event)
    trigger_plan_requested = bool(args.triggers)
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
            "Created bait files for trigger coverage: " + ", ".join(bait_files_created),
            status="completed",
        )
    return mon


def make_page_callbacks(mon, page_ref, *, deps):
    """Build ``(on_page_reloaded, ui_blocker_probe)`` for retry-on-crash."""

    def _on_page_reloaded(reloaded_page) -> None:
        page_ref.value = reloaded_page
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

    return _on_page_reloaded, _probe_ui_blocker


def dispatch_execution(
    page_ref,
    browser,
    args,
    mon,
    trigger_payload,
    planned_scenarios,
    execution_mode,
    *,
    deps,
):
    """Run one of six execution modes; return ``(execution_result, exit_code)``.

    Modes: ``demo`` / ``skip_automation`` / ``layered_passes`` /
    ``selected_scenarios`` / ``single_scenario`` / default-all
    (``run_all_scenarios``). Page rebinds during retry-on-crash flow
    through ``page_ref``.
    """
    on_page_reloaded, probe_ui_blocker = make_page_callbacks(mon, page_ref, deps=deps)
    exit_code = 0
    execution_result = _empty_execution_result(
        deps=deps, requested_scenarios=planned_scenarios
    )

    if args.demo:
        _run_demo_for_deps(page_ref.value, deps=deps)
        execution_result = _empty_execution_result(
            deps=deps, requested_scenarios=["demo"]
        )
        execution_result.executed_scenarios = ["demo"]
    elif execution_mode == "skip_automation":
        print("[*] Skipping automation scenario execution by request...")
    elif execution_mode == "layered_passes":
        print("[*] Running layered stimulus plan...")
        execution_result = _normalize_execution_result(
            deps.stimulus.run_stimulus_plan(
                page_ref.value, trigger_payload, monitor=mon
            ),
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
                page_ref.value,
                monitor=mon,
                event_recorder=mon.record_automation_event,
            )
    elif execution_mode == "selected_scenarios":
        print(f"[*] Running selected scenarios: {planned_scenarios}")
        execution_result = _normalize_execution_result(
            deps.automation.run_selected_scenarios(
                page_ref.value,
                planned_scenarios,
                shuffle=args.shuffle,
                retry_on_crash=args.retry_on_crash,
                browser=browser,
                on_page_reloaded=on_page_reloaded,
                ui_blocker_probe=probe_ui_blocker,
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
                page_ref.value,
                monitor=mon,
                event_recorder=mon.record_automation_event,
            )
    elif execution_mode == "single_scenario":
        scenario_name = planned_scenarios[0]
        print(f"[*] Running scenario: {scenario_name}")
        execution_result = _normalize_execution_result(
            deps.automation.run_selected_scenarios(
                page_ref.value,
                [scenario_name],
                shuffle=False,
                retry_on_crash=args.retry_on_crash,
                browser=browser,
                on_page_reloaded=on_page_reloaded,
                ui_blocker_probe=probe_ui_blocker,
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
                page_ref.value,
                shuffle=args.shuffle,
                retry_on_crash=args.retry_on_crash,
                browser=browser,
                on_page_reloaded=on_page_reloaded,
                ui_blocker_probe=probe_ui_blocker,
            ),
            deps=deps,
            requested_scenarios=deps.automation.list_scenarios(),
        )
        if execution_result.failed_scenarios:
            print("[!] Failed scenarios:")
            for name in execution_result.failed_scenarios:
                print(f"  - {name}")
            exit_code = 1

    return execution_result, exit_code


def apply_extra_triggers_if_needed(
    page_ref, args, mon, trigger_payload, execution_result, *, deps
) -> int:
    """Run extra triggers for payloads without ``stimulus_passes``. Returns 0 or 1."""
    if not trigger_payload or trigger_payload.stimulus_passes:
        return 0
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
        page_ref.value,
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
        return 1
    return 0


def summarize_skipped_scenarios_if_needed(execution_mode, execution_result) -> int:
    """Print skipped scenarios summary for selected/single modes. Returns 0 or 1."""
    if execution_mode not in {"selected_scenarios", "single_scenario"}:
        return 0
    if not execution_result.skipped_scenarios:
        return 0
    if execution_result.executed_scenarios:
        return 0
    print("[!] Skipped scenarios:")
    for item in execution_result.skipped_scenarios:
        print(f"  - {item.name}: {item.reason_code}")
    return 1


def finalize_monitor_report(mon, execution_result, exit_code, args) -> None:
    """Stop monitor + record runner status + save report. No-op when ``mon`` is None."""
    if mon is None:
        return
    print("[*] Collecting monitoring data...")
    if hasattr(mon, "record_execution_result"):
        mon.record_execution_result(execution_result)
    else:
        mon.report.requested_scenarios = list(execution_result.requested_scenarios)
        mon.report.extra_trigger_failures = list(
            execution_result.extra_trigger_failures
        )
        mon.record_failed_scenarios(execution_result.failed_scenarios)
        mon.report.scenarios_run = list(execution_result.executed_scenarios)
    report = mon.stop()
    # W11-3: surface the runner outcome on the report before the final disk
    # write so analysts can correlate ``runner_exit_code`` / ``runner_status``
    # with the run that produced the activation evidence. exit_code is
    # finalized by every code path that mutates it before this call.
    mon.set_runner_status(exit_code)
    report.print_summary()
    report.save(args.report_path)
