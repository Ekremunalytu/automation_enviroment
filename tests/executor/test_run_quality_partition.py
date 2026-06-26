"""W26 / Stream 3 (B6): run-quality reason-code partition.

``build_run_quality_partition`` buckets the automation-health reason codes into
behavioral (what the extension did) vs harness_health (how cleanly the sandbox
ran), with ``residual_variance`` the timing-sensitive subset of harness_health.
The partition is a pure function of the supplied health reasons — so it is
reproducible whenever the health reasons are.
"""

from __future__ import annotations

from types import SimpleNamespace

from executor.flows.playwright.health.summary import build_run_quality_partition


def _report(mode: str = "") -> SimpleNamespace:
    return SimpleNamespace(trigger_execution_mode=mode, log_file_path="")


def test_partition_splits_behavioral_from_harness_health() -> None:
    health = {
        "reasons": [
            "scenario_failures_present",  # behavioral
            "extension_host_log_missing",  # harness + residual
            "target_activation_missing",  # behavioral
            "harness_ready_marker_missing",  # harness, NOT residual
        ]
    }
    part = build_run_quality_partition(_report(), health)

    # Order follows the (deterministic) reasons list.
    assert part["behavioral"] == [
        "scenario_failures_present",
        "target_activation_missing",
    ]
    assert part["harness_health"] == [
        "extension_host_log_missing",
        "harness_ready_marker_missing",
    ]
    # residual_variance is the timing-sensitive subset of harness_health.
    assert part["residual_variance"] == ["extension_host_log_missing"]
    assert set(part["residual_variance"]).issubset(set(part["harness_health"]))
    assert not (set(part["behavioral"]) & set(part["harness_health"]))


def test_partition_residual_variance_covers_timing_sensitive_codes() -> None:
    health = {
        "reasons": [
            "target_stream_missing",
            "strong_target_attribution_missing",
            "harness_ready_marker_stale",
            "harness_activation_timeout",
            "extension_host_output_missing",
        ]
    }
    part = build_run_quality_partition(_report(), health)
    # All five are timing-sensitive harness-health reasons → all residual.
    assert part["residual_variance"] == health["reasons"]
    assert part["behavioral"] == []


def test_partition_skip_automation_is_empty() -> None:
    part = build_run_quality_partition(
        _report("skip_automation"),
        {"reasons": ["scenario_failures_present"]},
    )
    assert part == {"behavioral": [], "harness_health": [], "residual_variance": []}


def test_partition_is_deterministic_for_same_reasons() -> None:
    health = {
        "reasons": [
            "target_stream_missing",
            "verification_gap_present",
            "strong_target_attribution_missing",
        ]
    }
    report = _report()
    assert build_run_quality_partition(report, health) == build_run_quality_partition(
        report, health
    )
