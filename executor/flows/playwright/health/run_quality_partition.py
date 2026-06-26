"""Run-quality reason-code partition (W26 / Stream 3, B6).

Split out of ``summary.py`` (executor hotspot LoC ratchet): the partition is a
pure function over ``build_automation_health``'s reason codes, separable from the
run-quality discriminator it sits beside. It buckets the codes so the operator
(and a reproducibility test) can tell what the *extension* did (behavioral —
stable for the same bytes) from how cleanly the *sandbox/harness* ran
(harness-health — can vary with timing). ``residual_variance`` is the
timing-sensitive subset of harness-health (the flicker surface S6 hardens),
surfaced as a labeled band rather than a silent ``run_quality`` demotion.
"""

from __future__ import annotations

from typing import Any

from .summary import build_automation_health

_BEHAVIORAL_REASON_CODES = frozenset(
    {
        "target_extension_not_observed",
        "target_activation_missing",
        "scenario_failures_present",
        "skipped_scenarios_present",
        "extra_trigger_failures_present",
        "verification_gap_present",
    }
)
# Subset of the harness-health bucket (everything not behavioral) that is
# timing-sensitive and therefore the residual-variance band. Restricted to the
# codes ``build_automation_health`` can actually append to ``health["reasons"]``
# (the partition filters only that list). ``harness_ready_marker_stale`` and
# ``harness_activation_timeout`` are deliberately NOT here: they only ever
# surface as an event-attempt ``failure_reason_code`` that lands on a
# ``SkippedScenarioRecord`` -> the behavioral ``skipped_scenarios_present`` code,
# never into ``health["reasons"]``. A reachability test
# (``test_run_quality_partition``) pins this so the band cannot readmit an
# unreachable code.
_RESIDUAL_VARIANCE_REASON_CODES = frozenset(
    {
        "extension_host_log_missing",
        "extension_host_output_missing",
        "target_stream_missing",
        "strong_target_attribution_missing",
    }
)


def build_run_quality_partition(
    report: Any,
    automation_health: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Partition the automation-health reason CODES (B6, W26 / Stream 3).

    Returns ``{"behavioral": [...], "harness_health": [...], "residual_variance":
    [...]}`` — the same reason codes ``build_run_quality`` consumes. Pure over the
    supplied/derived ``automation_health`` reason codes, so the partition is
    reproducible whenever the health reasons are; order follows the
    (deterministic) reasons list.
    """
    execution_mode = str(getattr(report, "trigger_execution_mode", "")).strip()
    if execution_mode == "skip_automation":
        return {"behavioral": [], "harness_health": [], "residual_variance": []}
    health = automation_health or build_automation_health(
        report,
        extension_host_log_found=bool(getattr(report, "log_file_path", "")),
        extension_host_log_present=bool(getattr(report, "log_file_path", "")),
    )
    codes = [str(code) for code in health.get("reasons", []) or []]
    return {
        "behavioral": [c for c in codes if c in _BEHAVIORAL_REASON_CODES],
        "harness_health": [c for c in codes if c not in _BEHAVIORAL_REASON_CODES],
        "residual_variance": [c for c in codes if c in _RESIDUAL_VARIANCE_REASON_CODES],
    }
