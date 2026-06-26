"""W26 / Stream 3 (B6): run-quality reason-code partition.

``build_run_quality_partition`` buckets the automation-health reason codes into
behavioral (what the extension did) vs harness_health (how cleanly the sandbox
ran), with ``residual_variance`` the timing-sensitive subset of harness_health.
The partition is a pure function of the supplied health reasons — so it is
reproducible whenever the health reasons are.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from executor.flows.playwright.health.summary import (
    _BEHAVIORAL_REASON_CODES,
    _RESIDUAL_VARIANCE_REASON_CODES,
    build_run_quality_partition,
)


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


def test_partition_residual_variance_covers_reachable_timing_codes() -> None:
    # W26 / Stream 3 (B6, refined 2026-06-26): the band is the four codes
    # build_automation_health can actually append to health["reasons"].
    health = {
        "reasons": [
            "extension_host_log_missing",
            "extension_host_output_missing",
            "target_stream_missing",
            "strong_target_attribution_missing",
        ]
    }
    part = build_run_quality_partition(_report(), health)
    assert part["residual_variance"] == health["reasons"]
    assert part["behavioral"] == []


def test_partition_excludes_unreachable_harness_handshake_codes() -> None:
    # harness_ready_marker_stale / harness_activation_timeout only ever surface
    # as an attempt failure_reason_code -> behavioral skipped_scenarios_present,
    # never into health["reasons"], so they are NOT in the residual band.
    part = build_run_quality_partition(
        _report(),
        {"reasons": ["harness_ready_marker_stale", "harness_activation_timeout"]},
    )
    assert part["residual_variance"] == []


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


def _build_automation_health_reachable_codes() -> set[str]:
    """The reason-code literals ``build_automation_health`` can append to
    ``health["reasons"]`` (the only list the partition filters). Excludes the
    ``medium_reasons`` list in ``build_run_quality``.
    """
    summary_path = (
        Path(__file__).resolve().parents[2]
        / "executor"
        / "flows"
        / "playwright"
        / "health"
        / "summary.py"
    )
    tree = ast.parse(summary_path.read_text(encoding="utf-8"))
    reachable: set[str] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.FunctionDef) and node.name == "build_automation_health"
        ):
            continue
        for call in ast.walk(node):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "append"
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "reasons"
            ):
                for arg in call.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        reachable.add(arg.value)
    return reachable


def test_partition_code_sets_are_reachable() -> None:
    """W26 / Stream 3 (B6): both partition code sets must be subsets of the
    reasons build_automation_health can actually append, so the band can never
    silently declare an unreachable (dead) code — the drift the 2026-06-26
    verification workflow found (harness_ready_marker_stale /
    harness_activation_timeout were declared residual but never appended).
    """
    reachable = _build_automation_health_reachable_codes()
    assert reachable, "no reasons.append('<code>') literals found — guard is a shell"
    assert reachable >= _RESIDUAL_VARIANCE_REASON_CODES, (
        "residual_variance codes not appendable by build_automation_health: "
        f"{sorted(_RESIDUAL_VARIANCE_REASON_CODES - reachable)}"
    )
    assert reachable >= _BEHAVIORAL_REASON_CODES, (
        "behavioral codes not appendable by build_automation_health: "
        f"{sorted(_BEHAVIORAL_REASON_CODES - reachable)}"
    )
