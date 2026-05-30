"""In-house static detection runner (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.runner.run_detection``: loads the production
rules, evaluates each over the parsed VSIX context, and rolls findings up into a
``StaticDetectionReport`` with a per-tool execution record. Runs inside the
hardened ``automation_static_analyzer`` image, so imports stay within
``packages.analysis_contracts`` + ``static_runtime``.

``entrypoint.run_static_detection`` is the thin file-writing wrapper around this;
the CLI flag surface and on-disk JSON contract are frozen at the container
boundary (ES-2), so this swaps in behind them without reshaping either.
"""

from __future__ import annotations

import time

from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticSeverityCounts,
    StaticToolExecutionRecord,
)
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.registry import get_production_rules

# A misbehaving rule must degrade to "no finding", never crash the whole pass
# (parity with packages.analysis_engine.runner._RULE_EVALUATION_ERRORS).
_RULE_EVALUATION_ERRORS = (AttributeError, KeyError, TypeError, ValueError, OSError)


def _rollup_severity(findings: list[StaticDetectionFinding]) -> StaticSeverityCounts:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in findings:
        tier = finding.severity.value
        if tier in counts:
            counts[tier] += 1
    return StaticSeverityCounts(**counts)


def run_static_detection_engine(
    *,
    vsix_dir: str,
    rules_version: str,
    timeout_budget_s: int,
) -> StaticDetectionReport:
    """Run the in-house static rules over ``vsix_dir`` and return a report.

    ``timeout_budget_s`` is a soft wall-clock budget: the runner checks it
    between rules and stops early (emitting a partial but valid report) rather
    than letting a slow rule blow the docker-exec wall-clock the host caps.
    """
    start = time.monotonic()
    context = StaticAnalysisContext.from_vsix_dir(vsix_dir)
    rules = get_production_rules()

    findings: list[StaticDetectionFinding] = []
    for rule in rules:
        if timeout_budget_s > 0 and (time.monotonic() - start) > timeout_budget_s:
            break
        try:
            findings.extend(rule.evaluate(context))
        except _RULE_EVALUATION_ERRORS:
            # Skip the offending rule; the rest of the pass still contributes.
            continue

    duration_ms = int((time.monotonic() - start) * 1000)
    tool_execution = StaticToolExecutionRecord(
        tool="inhouse",
        version=rules_version or "0.0.0",
        rules_loaded=len(rules),
        findings_emitted=len(findings),
        duration_ms=duration_ms,
    )
    return StaticDetectionReport(
        findings=findings,
        tool_executions=[tool_execution],
        severity_counts=_rollup_severity(findings),
    )


__all__ = ["run_static_detection_engine"]
