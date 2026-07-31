"""Static pre-check decision gate + container runner (ES-3b core, ADR 0016).

The additive, orchestrator-free core of the static pre-check stage:

* ``evaluate_static_gate`` — the four-way conclusion truth table over a
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

from pydantic import ValidationError

from appcore.contracts.schema_defs.analysis_bundle import AnalysisBundle
from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
)
from executor.static_control import (
    StaticAnalyzerControl,
    default_static_analyzer_control,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionReport,
)
from packages.analysis_contracts.static_detection.policy import (
    _PROMOTED_HIGH_BLOCKERS as _PROMOTED_HIGH_BLOCKERS,
)
from packages.analysis_contracts.static_detection.policy import (
    evaluate_static_gate,
)


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


class StaticReportError(RuntimeError):
    """Raised when the static analyzer's emitted report cannot be read or parsed.

    A missing, truncated, malformed, or schema-invalid report is a tool failure,
    not a clean result. Raising here fails the static stage **closed** — the
    extension does not proceed to the dynamic sandbox on an unreadable report —
    so a broken analyzer can never be mistaken for an ALLOW.
    """


def run_static_analysis(
    *,
    vsix_dir: str,
    report_path: str,
    host_report_path: str | Path,
    rules_version: str,
    timeout_budget_s: int,
    control: StaticAnalyzerControl = default_static_analyzer_control,
    vsix_sha256: str = "",
) -> StaticAnalysisReport:
    """Run the static analyzer container and fold in the gate outcome.

    ``report_path`` is the container-side path the analyzer writes to (on the
    shared ``/results`` mount); ``host_report_path`` is where the host reads the
    emitted JSON back. The orchestrator stage derives both from config and
    injects the live ``control``; they are explicit params here so this core
    stays settings-free and unit-testable. ``vsix_sha256`` (W26 / B5) is threaded
    into the container so the emitted report is bound to the analyzed bytes.
    """
    control.run_static_analysis(
        vsix_dir=vsix_dir,
        report_path=report_path,
        rules_version=rules_version,
        timeout_budget_s=timeout_budget_s,
        vsix_sha256=vsix_sha256,
    )
    try:
        raw = Path(host_report_path).read_text(encoding="utf-8")
        detection_report = StaticDetectionReport.model_validate(json.loads(raw))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        # Fail closed: an unreadable / malformed / schema-invalid report is a tool
        # failure, never a silent ALLOW.
        raise StaticReportError(
            f"Static analyzer produced an unreadable report at "
            f"{host_report_path!r}: {exc}"
        ) from exc
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
    "StaticReportError",
    "build_combined_bundle",
    "evaluate_static_gate",
    "run_static_analysis",
]
