from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

from health_summary import build_automation_health, build_run_quality  # noqa: E402
from monitor_records import ScenarioTrace  # noqa: E402
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
