"""In-house + Semgrep static detection runner (ES-3a/ES-4, ADR 0016).

Loads the production in-house rules and evaluates each over the parsed VSIX
context, then runs Semgrep over the same tree, and rolls both tools' findings up
into a single ``StaticDetectionReport`` with one ``StaticToolExecutionRecord``
per tool (in-house first, semgrep second). Runs inside the hardened
``automation_static_analyzer`` image, so imports stay within
``packages.analysis_contracts`` + ``static_runtime``.

``entrypoint.run_static_detection`` is the thin file-writing wrapper around this;
the CLI flag surface and on-disk JSON contract are frozen at the container
boundary (ES-2), so ES-4 grows the report content (a second tool record, schema
v2, the ``partial`` flag) without reshaping either.
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
from static_runtime.semgrep_runner import run_semgrep

# A misbehaving rule must degrade to "no finding", never crash the whole pass
# (parity with packages.analysis_engine.runner._RULE_EVALUATION_ERRORS).
_RULE_EVALUATION_ERRORS = (AttributeError, KeyError, TypeError, ValueError, OSError)

# Semgrep's outer wall-clock is the static budget minus what the (sub-second)
# in-house pass already spent, less a small serialization reserve.
_SEMGREP_WALL_RESERVE_S = 2
_MIN_SEMGREP_WALL_S = 5
# Used when there is no soft budget (timeout_budget_s <= 0): give semgrep a
# generous-but-bounded wall-clock.
_DEFAULT_SEMGREP_WALL_S = 25


def _rollup_severity(findings: list[StaticDetectionFinding]) -> StaticSeverityCounts:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in findings:
        tier = finding.severity.value
        if tier in counts:
            counts[tier] += 1
    return StaticSeverityCounts(**counts)


def _run_inhouse(
    context: StaticAnalysisContext, rules_version: str, timeout_budget_s: int
) -> tuple[list[StaticDetectionFinding], StaticToolExecutionRecord]:
    """Run the in-house rules; return their findings + an execution record.

    ``timeout_budget_s`` is a soft wall-clock budget checked between rules; a
    rule that raises degrades to no finding (recorded in ``errored_rule_ids``)
    rather than crashing the pass. Either an early budget break or a swallowed
    rule error marks the record ``partial`` so the degradation is observable.
    """
    start = time.monotonic()
    rules = get_production_rules()

    findings: list[StaticDetectionFinding] = []
    errored_rule_ids: list[str] = []
    budget_tripped = False
    for rule in rules:
        if timeout_budget_s > 0 and (time.monotonic() - start) > timeout_budget_s:
            budget_tripped = True
            break
        try:
            findings.extend(rule.evaluate(context))
        except _RULE_EVALUATION_ERRORS:
            # Skip the offending rule; the rest of the pass still contributes,
            # but record which rule degraded so it is not a silent gap.
            errored_rule_ids.append(rule.rule_id)
            continue

    duration_ms = int((time.monotonic() - start) * 1000)
    record = StaticToolExecutionRecord(
        tool="inhouse",
        version=rules_version or "0.0.0",
        rules_loaded=len(rules),
        findings_emitted=len(findings),
        duration_ms=duration_ms,
        status="partial" if (budget_tripped or errored_rule_ids) else "ok",
        error_count=len(errored_rule_ids),
        errored_rule_ids=sorted(set(errored_rule_ids)),
    )
    return findings, record


def _semgrep_wall_timeout(timeout_budget_s: int, start: float) -> int:
    """Hard outer wall-clock (seconds) for the semgrep subprocess."""
    if timeout_budget_s <= 0:
        return _DEFAULT_SEMGREP_WALL_S
    remaining = int(
        timeout_budget_s - (time.monotonic() - start) - _SEMGREP_WALL_RESERVE_S
    )
    return max(_MIN_SEMGREP_WALL_S, remaining)


def run_static_detection_engine(
    *,
    vsix_dir: str,
    rules_version: str,
    timeout_budget_s: int,
    semgrep_enabled: bool = True,
    vsix_sha256: str = "",
) -> StaticDetectionReport:
    """Run the in-house rules + Semgrep over ``vsix_dir`` and return a report.

    The in-house pass runs first (cheap), then Semgrep gets the remaining budget
    as its hard subprocess wall-clock. ``tool_executions`` is ordered
    ``[inhouse, semgrep]``. ``semgrep_enabled=False`` skips the Semgrep pass — an
    escape hatch for environments without the wheel and for in-house-only tests.
    The report is ``partial`` when either tool ran only partially.
    """
    start = time.monotonic()
    context = StaticAnalysisContext.from_vsix_dir(vsix_dir)

    inhouse_findings, inhouse_record = _run_inhouse(
        context, rules_version, timeout_budget_s
    )
    findings: list[StaticDetectionFinding] = list(inhouse_findings)
    tool_executions: list[StaticToolExecutionRecord] = [inhouse_record]
    partial = inhouse_record.status != "ok"

    if semgrep_enabled:
        semgrep_result = run_semgrep(
            vsix_dir=vsix_dir,
            wall_timeout_s=_semgrep_wall_timeout(timeout_budget_s, start),
        )
        findings.extend(semgrep_result.findings)
        tool_executions.append(semgrep_result.record)
        partial = partial or semgrep_result.record.status != "ok"

    return StaticDetectionReport(
        findings=findings,
        tool_executions=tool_executions,
        severity_counts=_rollup_severity(findings),
        partial=partial,
        # W26 / Stream 3 (B5): bind the static report to the analyzed bytes.
        vsix_sha256=vsix_sha256,
    )


__all__ = ["run_static_detection_engine"]
