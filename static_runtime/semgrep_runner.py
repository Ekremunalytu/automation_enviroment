"""Semgrep tool runner for the static pre-check (ES-4, ADR 0016 §Decision 4).

Runs Semgrep over the decompressed VSIX source tree as a *second* static tool
writing into the same ``StaticDetectionReport`` as the in-house rules. Mirrors
``static_runner``'s discipline: imports stay within the standard library,
``subprocess``, and ``packages.analysis_contracts`` so the hardened
``automation_static_analyzer`` image needs no dynamic-engine import (the
``static_runtime`` boundary, pinned by
``tests/architecture/test_static_runtime_import_boundary.py``).

Semgrep runs fully offline (``--metrics=off``; the container is
``network_mode: none``). A non-zero exit, a timeout, or unparseable output never
raises out of :func:`run_semgrep`: it degrades to a ``StaticToolExecutionRecord``
with ``status`` in {``error``, ``timeout``} and zero findings, so a Semgrep
outage cannot crash the pass or be mistaken for a clean ALLOW — the in-house
findings (which drive the gate) are always still written.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticToolExecutionRecord,
)
from static_runtime.rules._common import file_evidence

# The interpreter that launched ``python -m static_runtime`` — in the hardened
# image the pinned ``/usr/local/bin/python3``. Semgrep's console script installs
# next to it, so deriving the launcher from ``sys.executable`` keeps it absolute
# and immune to a tampered $PATH (mirrors executor.binary_paths' discipline)
# without guessing whether ``python -m semgrep`` is supported.
_PYTHON = sys.executable or "/usr/local/bin/python3"
_SEMGREP_BIN = str(Path(_PYTHON).parent / "semgrep")

# Rule files ship inside static_runtime/ (already COPYed into the image).
_RULES_DIR = Path(__file__).resolve().parent / "semgrep_rules"

# EXACT semgrep pin; MUST equal the docker/static_analyzer/requirements.txt pin
# (tests/architecture/test_semgrep_pin_consistency.py) so the recorded version
# can never drift from the installed wheel.
_SEMGREP_VERSION = "1.164.0"

_RULE_VERSION = "1.0.0"

# Per-rule-per-file Semgrep timeout (seconds). The in-house runner's cooperative
# inter-rule budget cannot interrupt a single semgrep subprocess, so semgrep gets
# its own hard bounds: this per-rule cap plus the outer subprocess wall-clock the
# caller derives from the remaining static budget.
_SEMGREP_PER_RULE_TIMEOUT_S = 5

# Skip files larger than this (minified/bundled payloads): bounds scan time and
# mirrors the in-house "oversized text" posture. Oversize files land in semgrep's
# ``paths.skipped`` (not ``errors``), so they do not mark the report partial.
_MAX_TARGET_BYTES = 1_000_000

# Cap total mapped findings so a pathological tree cannot bloat the report.
_MAX_FINDINGS = 200

_SEMGREP_MEMORY_MB = 768

# Outer subprocess wall-clock floor (seconds) even when the inherited budget is
# tiny, so semgrep always gets a fair chance to start.
_MIN_WALL_TIMEOUT_S = 5

# Exit codes semgrep uses for a successful run: 0 = no findings, 1 = findings.
# >= 2 is a tool/config error.
_SEMGREP_OK_RETURNCODES = frozenset({0, 1})

# Mirror of StaticToolExecutionRecord.status's Literal.
_ToolStatus = Literal["ok", "partial", "error", "timeout"]


@dataclass(frozen=True, slots=True)
class _SemgrepRuleMeta:
    """The contract-side identity of one Semgrep rule, keyed by its bare id."""

    rule_id: str
    categories: tuple[str, ...]
    title: str
    description: str
    mitigation_hint: str


# Keyed by the Semgrep rule's bare ``id`` (the trailing dotted segment of the
# emitted ``check_id``). The runner takes severity/confidence/categories/title
# from here — never from Semgrep's output — so the four findings are fully
# deterministic and contract-valid regardless of what the YAML emits.
_RULE_META: dict[str, _SemgrepRuleMeta] = {
    "eval": _SemgrepRuleMeta(
        rule_id="extrace.sg.eval",
        categories=("attack.T1059", "extrace.ext.dynamic_code_exec"),
        title="Dynamic code execution via eval()",
        description=(
            "The extension calls eval(), executing a string as code. This is a "
            "common vehicle for running attacker-controlled payloads and defeats "
            "static review of the executed logic."
        ),
        mitigation_hint=(
            "Avoid eval(); evaluating dynamic strings as code is rarely necessary "
            "and is a primary code-injection vector."
        ),
    ),
    "function_constructor": _SemgrepRuleMeta(
        rule_id="extrace.sg.function_constructor",
        categories=("attack.T1059", "extrace.ext.dynamic_code_exec"),
        title="Dynamic code execution via the Function constructor",
        description=(
            "The extension builds a function from a string with the Function "
            "constructor, an eval()-equivalent dynamic-execution primitive."
        ),
        mitigation_hint=(
            "Avoid constructing functions from strings; it is equivalent to "
            "eval() for code-injection purposes."
        ),
    ),
    "child_process": _SemgrepRuleMeta(
        rule_id="extrace.sg.child_process",
        categories=("attack.T1059", "extrace.ext.process_spawn"),
        title="OS process execution via child_process",
        description=(
            "The extension uses the child_process module to spawn operating-"
            "system processes, a direct path to arbitrary command execution "
            "outside the JavaScript sandbox."
        ),
        mitigation_hint=(
            "Confirm the extension genuinely needs to spawn processes; "
            "child_process is a primary command-execution vector."
        ),
    ),
    "vm_runincontext": _SemgrepRuleMeta(
        rule_id="extrace.sg.vm_runincontext",
        categories=("attack.T1059", "extrace.ext.dynamic_code_exec"),
        title="Dynamic code execution via the vm module",
        description=(
            "The extension runs a string of code through the vm module "
            "(runInContext / runInNewContext / runInThisContext), another "
            "eval()-equivalent execution primitive."
        ),
        mitigation_hint=(
            "Avoid vm.runInContext and its variants for untrusted input; they "
            "execute arbitrary code."
        ),
    ),
}


@dataclass(slots=True)
class SemgrepRunResult:
    """Mapped Semgrep findings plus the tool-execution record for the report."""

    findings: list[StaticDetectionFinding]
    record: StaticToolExecutionRecord


def run_semgrep(
    *,
    vsix_dir: str,
    wall_timeout_s: int,
    per_rule_timeout_s: int = _SEMGREP_PER_RULE_TIMEOUT_S,
) -> SemgrepRunResult:
    """Run Semgrep over ``vsix_dir`` and return mapped findings + a tool record.

    Never raises for a Semgrep failure (non-zero exit, timeout, unparseable
    output): such failures yield a record with ``status`` in {``error``,
    ``timeout``} and zero findings. ``wall_timeout_s`` is the hard outer
    subprocess bound (derived by the caller from the remaining static budget);
    ``per_rule_timeout_s`` is Semgrep's internal per-rule-per-file cap. The
    record's ``version`` is always the pinned Semgrep wheel version (what makes
    its findings reproducible), not the in-house ruleset version.
    """
    start = time.monotonic()
    vsix_root = Path(vsix_dir)
    rules_loaded = _count_rules()
    version = _SEMGREP_VERSION

    argv = _build_argv(vsix_dir=vsix_dir, per_rule_timeout_s=per_rule_timeout_s)
    try:
        completed = subprocess.run(  # noqa: S603  # nosec B603
            argv,
            capture_output=True,
            text=True,
            timeout=max(_MIN_WALL_TIMEOUT_S, wall_timeout_s),
            env=_build_env(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="timeout"
        )
    except OSError:
        # Launcher missing / not executable in this environment — degrade,
        # never crash the static pass.
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="error"
        )

    if completed.returncode not in _SEMGREP_OK_RETURNCODES:
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="error"
        )

    try:
        results, errors = _parse_results(completed.stdout)
    except (json.JSONDecodeError, ValueError):
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="error"
        )

    findings: list[StaticDetectionFinding] = []
    for raw in results:
        if len(findings) >= _MAX_FINDINGS:
            break
        finding = _map_result_to_finding(raw, vsix_root)
        if finding is not None:
            findings.append(finding)

    duration_ms = int((time.monotonic() - start) * 1000)
    record = StaticToolExecutionRecord(
        tool="semgrep",
        version=version,
        rules_loaded=rules_loaded,
        findings_emitted=len(findings),
        duration_ms=duration_ms,
        # Per-file parse errors / rule timeouts mean incomplete coverage — mark
        # the run partial (and surface the count) without failing it.
        status="partial" if errors else "ok",
        error_count=len(errors),
        errored_rule_ids=_collect_error_rule_ids(errors),
    )
    return SemgrepRunResult(findings=findings, record=record)


def _build_argv(*, vsix_dir: str, per_rule_timeout_s: int) -> list[str]:
    return [
        _SEMGREP_BIN,
        "scan",
        "--config",
        str(_RULES_DIR),
        "--json",
        "--metrics=off",
        "--disable-version-check",
        "--quiet",
        "--no-git-ignore",
        "--jobs",
        "1",
        "--max-memory",
        str(_SEMGREP_MEMORY_MB),
        "--max-target-bytes",
        str(_MAX_TARGET_BYTES),
        "--timeout",
        str(per_rule_timeout_s),
        "--timeout-threshold",
        "0",
        "--exclude",
        "node_modules",
        "--exclude",
        "*.min.js",
        vsix_dir,
    ]


def _build_env() -> dict[str, str]:
    """Minimal, explicit, offline environment (does not inherit the parent env).

    HOME / cache are pinned to the non-root ``static`` user's writable home so the
    pass is deterministic and never reaches the network.
    """
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/home/static",
        "SEMGREP_SEND_METRICS": "off",
        "SEMGREP_ENABLE_VERSION_CHECK": "0",
        "XDG_CACHE_HOME": "/home/static/.cache",
        "PYTHONUNBUFFERED": "1",
    }


def _parse_results(stdout: str) -> tuple[list[dict], list[dict]]:
    """Extract ``(results, errors)`` from Semgrep's ``--json`` stdout."""
    payload = json.loads(stdout)
    if not isinstance(payload, dict):
        raise ValueError("semgrep output is not a JSON object")
    results = payload.get("results", [])
    errors = payload.get("errors", [])
    if not isinstance(results, list) or not isinstance(errors, list):
        raise ValueError("semgrep results/errors are not lists")
    return results, errors


def _map_result_to_finding(
    raw: object, vsix_root: Path
) -> StaticDetectionFinding | None:
    """Map one Semgrep result dict to a finding, or None to skip it."""
    if not isinstance(raw, dict):
        return None
    check_id = raw.get("check_id")
    if not isinstance(check_id, str) or not check_id:
        return None
    meta = _RULE_META.get(_bare_id(check_id))
    if meta is None:
        # Only our four rules map; anything else is unexpected — skip it rather
        # than mislabel it.
        return None

    relative_path = _relative_path(raw.get("path"), vsix_root)
    if relative_path is None:
        return None

    extra = raw.get("extra")
    extra = extra if isinstance(extra, dict) else {}
    lines = extra.get("lines")
    snippet = lines if isinstance(lines, str) and lines else None

    evidence = file_evidence(
        relative_path,
        "source_file",
        snippet=snippet,
        tool="semgrep",
        line_number=_line_number(raw.get("start")),
        rule_match_id=check_id,
    )
    return StaticDetectionFinding(
        rule_id=meta.rule_id,
        rule_version=_RULE_VERSION,
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=list(meta.categories),
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        title=meta.title,
        description=meta.description,
        evidence=[evidence],
        mitigation_hint=meta.mitigation_hint,
    )


def _bare_id(check_id: str) -> str:
    """The trailing dotted segment of a Semgrep check_id (our rule's bare id).

    Robust to whatever path prefix Semgrep prepends for a directory ``--config``
    (e.g. ``semgrep_rules.extrace-vsix-js.eval`` -> ``eval``).
    """
    return check_id.rsplit(".", 1)[-1]


def _relative_path(path: object, vsix_root: Path) -> str | None:
    """Make a Semgrep result path relative to the scan root, or None to skip.

    The contract validator additionally rejects absolute / ``..`` / control-char
    paths; this pre-filter turns a surprising path into a skipped finding rather
    than a raised validation error.
    """
    if not isinstance(path, str) or not path:
        return None
    candidate = Path(path)
    try:
        relative = (
            candidate.relative_to(vsix_root) if candidate.is_absolute() else candidate
        )
    except ValueError:
        return None
    rel_str = relative.as_posix()
    if not rel_str or rel_str.startswith(("/", "\\")):
        return None
    if any(segment == ".." for segment in rel_str.split("/")):
        return None
    return rel_str


def _line_number(start: object) -> int | None:
    if isinstance(start, dict):
        line = start.get("line")
        if isinstance(line, int) and line >= 1:
            return line
    return None


def _collect_error_rule_ids(errors: list[dict]) -> list[str]:
    """Deduped, sorted bare rule ids of any rule-level scan errors."""
    ids: set[str] = set()
    for err in errors:
        if not isinstance(err, dict):
            continue
        check_id = err.get("rule_id") or err.get("check_id")
        if isinstance(check_id, str) and check_id:
            meta = _RULE_META.get(_bare_id(check_id))
            ids.add(meta.rule_id if meta is not None else _bare_id(check_id))
    return sorted(ids)


def _count_rules() -> int:
    """Number of mappable rules for the tool record.

    ``_RULE_META`` is the source of truth for which rules the runner can map; the
    shipped YAML rule ids are asserted to match it in
    ``tests/security/test_semgrep_js_rules.py``, so its size is the honest count.
    """
    return len(_RULE_META)


def _failure_result(
    *, version: str, rules_loaded: int, start: float, status: _ToolStatus
) -> SemgrepRunResult:
    """A zero-finding result carrying a ``status`` of ``error`` / ``timeout``."""
    duration_ms = int((time.monotonic() - start) * 1000)
    return SemgrepRunResult(
        findings=[],
        record=StaticToolExecutionRecord(
            tool="semgrep",
            version=version,
            rules_loaded=rules_loaded,
            findings_emitted=0,
            duration_ms=duration_ms,
            status=status,
            error_count=0,
            errored_rule_ids=[],
        ),
    )


__all__ = ["SemgrepRunResult", "run_semgrep"]
