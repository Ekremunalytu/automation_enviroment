"""Static pre-check decision gate + container runner (ES-3b core, ADR 0016).

The additive, orchestrator-free core of the static pre-check stage:

* ``evaluate_static_gate`` — the block-and-warn truth table over a
  ``StaticDetectionReport`` (ADR 0016 §Decision 1).
* ``run_static_analysis`` — drives the hardened ``automation_static_analyzer``
  container through ``StaticAnalyzerControl``, parses the emitted
  ``StaticDetectionReport``, and folds in the gate outcome.
* ``build_combined_bundle`` — pairs the static report with the (optional)
  dynamic bundle; ``dynamic_bundle`` is ``None`` on the BLOCK / cheap-reject
  path.
* ``StaticAnalysisBlockedError`` — the public error the orchestrator raises
  when the gate blocks (defined here as part of this module's surface).

The job-step contract change (``empty_job_steps`` 5 -> 7), the
``analysis_service`` orchestrator wiring, the ``rejected_static`` DB
transition, the ``settings.static_analysis`` feature flag, and the
cancellation coordinator land in the follow-on orchestrator sub-step — this
module deliberately touches none of them, so it stays settings-free and
unit-testable.
"""

from __future__ import annotations

import json
from pathlib import Path

from appcore.contracts.schema_defs.analysis_bundle import AnalysisBundle
from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
from executor.static_control import (
    StaticAnalyzerControl,
    default_static_analyzer_control,
)
from packages.analysis_contracts.detection.enums import Severity
from packages.analysis_contracts.static_detection import (
    StaticDetectionReport,
    StaticGateDecision,
    StaticGateOutcome,
)

# Curated HIGH-severity rules promoted to a BLOCK decision. A frozenset, never
# config: changing it requires an ADR 0016 amendment + commit audit trail
# (ADR 0016 §Decision 1). Today the sole member is the static typosquat rule.
_PROMOTED_HIGH_BLOCKERS: frozenset[str] = frozenset({"extrace.s2.typosquat"})

# Severity tiers that warrant a WARN when nothing blocks. ADR 0016 §Decision 1
# enumerates LOW/MEDIUM -> warn; a HIGH finding that is not a promoted blocker
# rides the same WARN path. INFO is purely informational and does not, by
# itself, raise a warning.
_WARN_SEVERITIES: frozenset[Severity] = frozenset(
    {Severity.HIGH, Severity.MEDIUM, Severity.LOW}
)

_ALLOW_REASON_CLEAN = "No blocking or warnable static findings."


class StaticAnalysisBlockedError(RuntimeError):
    """Raised when the static gate BLOCKs an extension (terminal rejected_static).

    Carries the ``StaticAnalysisReport`` so the orchestrator can persist the
    combined bundle on the cheap-reject path. ``run_static_analysis`` never
    raises this — it always returns a full report so the BLOCK outcome can be
    serialized; the orchestrator inspects ``gate_outcome.decision`` and raises.
    """

    def __init__(self, message: str, *, static_report: StaticAnalysisReport) -> None:
        super().__init__(message)
        self.static_report = static_report


def _is_blocking(severity: Severity, rule_id: str) -> bool:
    """A finding blocks when it is CRITICAL or a promoted HIGH blocker."""
    if severity is Severity.CRITICAL:
        return True
    return severity is Severity.HIGH and rule_id in _PROMOTED_HIGH_BLOCKERS


def _dedupe(rule_ids: list[str]) -> list[str]:
    """Stable-sorted unique rule ids for a deterministic machine-readable cause."""
    return sorted(set(rule_ids))


def evaluate_static_gate(report: StaticDetectionReport) -> StaticGateOutcome:
    """Apply the ADR 0016 block-and-warn truth table to a detection report.

    * a CRITICAL finding, or a HIGH finding whose ``rule_id`` is in
      ``_PROMOTED_HIGH_BLOCKERS`` -> BLOCK (terminal ``rejected_static``);
    * otherwise any HIGH/MEDIUM/LOW finding -> WARN (the dynamic stage proceeds
      and the warnings ride along in the combined bundle);
    * no findings (or only INFO) -> ALLOW.

    ``blocked_by`` / ``warned_by`` carry the deduped, sorted ``rule_id`` set so
    the rejection/warning always names a machine-readable cause (the gate
    contract's observability invariant).
    """
    blocked_by = _dedupe(
        [f.rule_id for f in report.findings if _is_blocking(f.severity, f.rule_id)]
    )
    if blocked_by:
        return StaticGateOutcome(
            decision=StaticGateDecision.BLOCK, blocked_by=blocked_by
        )

    warned_by = _dedupe(
        [f.rule_id for f in report.findings if f.severity in _WARN_SEVERITIES]
    )
    if warned_by:
        return StaticGateOutcome(decision=StaticGateDecision.WARN, warned_by=warned_by)

    return StaticGateOutcome(
        decision=StaticGateDecision.ALLOW, allow_reason=_ALLOW_REASON_CLEAN
    )


def run_static_analysis(
    *,
    vsix_dir: str,
    report_path: str,
    host_report_path: str | Path,
    rules_version: str,
    timeout_budget_s: int,
    control: StaticAnalyzerControl = default_static_analyzer_control,
) -> StaticAnalysisReport:
    """Run the static analyzer container and fold in the gate outcome.

    ``report_path`` is the container-side path the analyzer writes to (on the
    shared ``/results`` mount); ``host_report_path`` is where the host reads the
    emitted JSON back. The orchestrator stage derives both from config and
    injects the live ``control``; they are explicit params here so this core
    stays settings-free and unit-testable.
    """
    control.run_static_analysis(
        vsix_dir=vsix_dir,
        report_path=report_path,
        rules_version=rules_version,
        timeout_budget_s=timeout_budget_s,
    )
    payload = json.loads(Path(host_report_path).read_text(encoding="utf-8"))
    detection_report = StaticDetectionReport.model_validate(payload)
    gate_outcome = evaluate_static_gate(detection_report)
    return StaticAnalysisReport(
        detection_report=detection_report, gate_outcome=gate_outcome
    )


def build_combined_bundle(
    static_report: StaticAnalysisReport,
    dynamic_bundle: AnalysisBundle | None = None,
) -> CombinedAnalysisBundle:
    """Pair the static report with the dynamic bundle (``None`` on the BLOCK path)."""
    return CombinedAnalysisBundle(
        static_report=static_report, dynamic_bundle=dynamic_bundle
    )


__all__ = [
    "StaticAnalysisBlockedError",
    "build_combined_bundle",
    "evaluate_static_gate",
    "run_static_analysis",
]
