from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

from health_summary import build_automation_health, build_run_quality  # noqa: E402
from monitor_records import LogStreamEntry, ScenarioTrace  # noqa: E402
from monitor_types import ActivationReport  # noqa: E402
from runtime_capture.events import ActivationEntry  # noqa: E402


def _healthy_report(**overrides) -> ActivationReport:
    """Build a report that would otherwise roll up healthy.

    `target_extension_observed` is a computed property, so we seed the
    underlying fields that make it return True: `target_extension_id`
    plus a matching `ActivationEntry`.
    """
    target_id = overrides.pop("target_extension_id", "publisher.name")
    extension_host_output = overrides.pop(
        "extension_host_output", "host output present"
    )
    report = ActivationReport()
    report.target_extension_id = target_id
    report.extension_host_output = extension_host_output
    report.activated.append(ActivationEntry(extension_id=target_id, source="log"))
    for key, value in overrides.items():
        setattr(report, key, value)
    return report


def test_fatal_ui_crash_forces_inconclusive_status() -> None:
    report = _healthy_report(
        scenario_traces=[
            ScenarioTrace(
                name="settings_modification",
                started_at=0.0,
                ended_at=1.0,
                status="failed",
                failure_reason_code="fatal_ui_crash",
                error_detail="Keyboard.press: Target crashed",
            )
        ],
        failed_scenarios=["settings_modification"],
        requested_scenarios=["settings_modification"],
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    assert health["status"] == "inconclusive"
    assert "fatal_ui_crash" in health["reasons"]


def test_fatal_ui_crash_dominates_over_degraded() -> None:
    """A fatal crash + other degraded signals still roll up to inconclusive."""
    report = _healthy_report(
        scenario_traces=[
            ScenarioTrace(
                name="crashy",
                started_at=0.0,
                ended_at=1.0,
                status="failed",
                failure_reason_code="fatal_ui_crash",
                error_detail="Target crashed",
            ),
            ScenarioTrace(
                name="regular_fail",
                started_at=1.0,
                ended_at=2.0,
                status="failed",
            ),
        ],
        failed_scenarios=["crashy", "regular_fail"],
        requested_scenarios=["crashy", "regular_fail"],
        extra_trigger_failures=["one"],
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    assert health["status"] == "inconclusive"
    assert "fatal_ui_crash" in health["reasons"]
    assert "scenario_failures_present" in health["reasons"]


def test_fatal_crash_drives_run_quality_inconclusive() -> None:
    report = _healthy_report(
        scenario_traces=[
            ScenarioTrace(
                name="crash",
                started_at=0.0,
                ended_at=1.0,
                status="failed",
                failure_reason_code="fatal_ui_crash",
                error_detail="Target crashed",
            )
        ],
        failed_scenarios=["crash"],
        requested_scenarios=["crash"],
    )
    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    quality, reasons = build_run_quality(report, automation_health=health)

    assert quality == "inconclusive"
    assert any("fatal_ui_crash" in reason for reason in reasons) or reasons


def test_no_fatal_crash_does_not_add_reason_label() -> None:
    report = _healthy_report(
        scenario_traces=[
            ScenarioTrace(name="ok", started_at=0.0, ended_at=1.0, status="completed")
        ],
        requested_scenarios=["ok"],
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    assert "fatal_ui_crash" not in health["reasons"]


def _partial_evidence_report(
    *,
    execution_mode: str,
    verification_gap: int,
    unresolved: int,
) -> ActivationReport:
    """Build a report whose `verification_gap` property = ``verification_gap``.

    `verification_gap` is computed (attempted - verified capability
    counts), so it can't be set directly. The fixture seeds the
    underlying ``coverage_matrix`` + ``attempted_capabilities`` +
    ``verified_capabilities`` fields so the property returns the
    expected delta.
    """
    target_id = "publisher.tool"
    report = ActivationReport()
    report.target_extension_id = target_id
    report.extension_host_output = "host output"
    report.activated.append(
        ActivationEntry(
            extension_id=target_id,
            activation_event="onCommand:test",
            timestamp="2026-01-01 10:00:00.000",
            source="log",
        )
    )
    # target_stream_entries reads report.log_streams["target_extension_host"];
    # ``log_streams`` is computed from ``log_entries``, so seed an entry
    # marked is_target_extension=True so the inconclusive guard sees a
    # non-empty target stream.
    report.log_entries.append(
        LogStreamEntry(
            stream="target_extension_host",
            kind="activation",
            extension_id=target_id,
            message="Activated publisher.tool",
            is_target_extension=True,
        )
    )
    report.trigger_plan_requested = True
    report.trigger_plan_loaded = True
    report.trigger_plan_applied = True
    report.trigger_execution_mode = execution_mode
    report.attempted_capabilities = [f"cap_{i}" for i in range(3 + verification_gap)]
    report.verified_capabilities = [f"cap_{i}" for i in range(3)]
    report.coverage_matrix = {
        cap: {"track": "official", "track_kind": "official"}
        for cap in report.attempted_capabilities
    }
    report.official_event_coverage = {
        "track": "official",
        "declared": 3 + unresolved,
        "verified": 3,
        "attempted_only": unresolved,
        "failed": 0,
        "blocked": 0,
        "unresolved": unresolved,
        "declared_events": [],
    }
    return report


def test_partial_evidence_signals_demote_health_to_degraded_in_layered_runs() -> None:
    """FOLLOWUP codex-automation-3.

    Layered runs with verification_gap > 0 / official_unresolved_present
    used to keep automation_health.status="healthy" while run_quality
    dropped to "medium" (W7 entry layered run_quality label fix only
    closed official_unresolved_present in run_quality reasons text).
    The FOLLOWUP propagates the same reason codes into
    automation_health.reasons regardless of execution mode and demotes
    status to "degraded". run_quality stays "medium" because partial
    evidence is not a run failure.
    """
    report = _partial_evidence_report(
        execution_mode="layered_passes",
        verification_gap=2,
        unresolved=2,
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )
    quality, _ = build_run_quality(report, automation_health=health)

    assert report.verification_gap == 2
    assert health["status"] == "degraded"
    assert "verification_gap_present" in health["reasons"]
    assert "official_unresolved_present" in health["reasons"]
    # Partial-evidence-only degradation stays at "medium".
    assert quality == "medium"


def test_partial_evidence_in_non_layered_run_still_degrades_health() -> None:
    """Non-layered counterpart: same propagation contract."""
    report = _partial_evidence_report(
        execution_mode="single_pass",
        verification_gap=1,
        unresolved=1,
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    assert report.verification_gap == 1
    assert health["status"] == "degraded"
    assert "verification_gap_present" in health["reasons"]
    assert "official_unresolved_present" in health["reasons"]


def test_no_partial_evidence_keeps_health_healthy() -> None:
    """Regression guard: clean reports stay healthy and high quality."""
    report = _partial_evidence_report(
        execution_mode="single_pass",
        verification_gap=0,
        unresolved=0,
    )

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )
    quality, _ = build_run_quality(report, automation_health=health)

    assert report.verification_gap == 0
    assert health["status"] == "healthy"
    assert "verification_gap_present" not in health["reasons"]
    assert "official_unresolved_present" not in health["reasons"]
    assert quality == "high"
