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

import hashlib
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
    StaticCoverageReason,
    StaticDetectionFinding,
    StaticScanCoverage,
    StaticToolExecutionRecord,
)
from static_runtime.artifacts import is_minified_path, is_vendor_path
from static_runtime.rules._common import MAX_TEXT_BYTES, file_evidence

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

# Keep Semgrep and the in-house text rules on the same bounded production-bundle
# envelope. This covers common multi-MiB webpack/esbuild entrypoints without
# allowing an extension-controlled file to drive an unbounded parser workload.
_MAX_TARGET_BYTES = MAX_TEXT_BYTES

# Cap total mapped findings so a pathological tree cannot bloat the report.
_MAX_FINDINGS = 200
_MAX_PATH_DETAILS = 20

_SEMGREP_MEMORY_MB = 768

# Outer subprocess wall-clock floor (seconds) even when the inherited budget is
# tiny, so semgrep always gets a fair chance to start.
_MIN_WALL_TIMEOUT_S = 5

# Exit codes semgrep uses for a successful run: 0 = no findings, 1 = findings.
# >= 2 is a tool/config error.
_SEMGREP_OK_RETURNCODES = frozenset({0, 1})

# Mirror of StaticToolExecutionRecord.status's Literal.
_ToolStatus = Literal["ok", "partial", "error", "timeout"]
_SEMGREP_SOURCE_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs"})
_BASE_EXCLUDED_PATTERNS = (
    "node_modules",
    "vendor",
    "vendors",
    "*.min.js",
    "*.min.jsx",
    "*.min.ts",
    "*.min.tsx",
    "*.min.cjs",
    "*.min.mjs",
)


@dataclass(frozen=True, slots=True)
class _SemgrepRuleMeta:
    """The contract-side identity of one Semgrep rule, keyed by its bare id."""

    rule_id: str
    categories: tuple[str, ...]
    title: str
    description: str
    mitigation_hint: str


@dataclass(frozen=True, slots=True)
class SemgrepRuleInventoryEntry:
    """Stable rule metadata used by the measurement-foundation inventory."""

    rule_id: str
    rule_version: str
    rule_lifecycle: str
    severity: str
    confidence: str
    categories: tuple[str, ...]
    capabilities: tuple[str, ...]
    gate_effect: str
    artifact_roles: tuple[str, ...]
    test_ownership: tuple[str, ...]
    positive_tests: tuple[str, ...]
    negative_tests: tuple[str, ...]
    known_false_positives: tuple[str, ...]
    known_blind_spots: tuple[str, ...]
    runtime_budget: str
    owner: str


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
    "outbound_net_module": _SemgrepRuleMeta(
        rule_id="extrace.sg.outbound_net_module",
        categories=("attack.T1071", "extrace.ext.outbound_network"),
        title="Raw network module import",
        description=(
            "The extension imports a raw network module (http / https / net / "
            "tls / dns / dgram), a direct outbound socket or request capability "
            "that bypasses the editor's vetted networking APIs and is a common "
            "command-and-control / exfiltration primitive."
        ),
        mitigation_hint=(
            "Confirm the extension genuinely needs raw network access; prefer "
            "the editor's networking APIs, which are observable and scoped."
        ),
    ),
    "dynamic_require": _SemgrepRuleMeta(
        rule_id="extrace.sg.dynamic_require",
        categories=("attack.T1027", "extrace.ext.dynamic_require"),
        title="Dynamic require of a computed module specifier",
        description=(
            "The extension calls require() with a non-literal specifier, so the "
            "loaded module is computed at runtime. This hides the dependency "
            "from static review and enables conditional loading of staged code."
        ),
        mitigation_hint=(
            "Use static, literal require()/import specifiers; a computed module "
            "path defeats dependency review."
        ),
    ),
    "base64_decode_exec": _SemgrepRuleMeta(
        rule_id="extrace.sg.base64_decode_exec",
        categories=("attack.T1027", "extrace.ext.dynamic_code_exec"),
        title="Decode-then-execute of a packed payload",
        description=(
            "The extension decodes a base64 / escaped payload and runs it via "
            "eval() or the Function constructor — a packing trick that smuggles "
            "executed logic past static review."
        ),
        mitigation_hint=(
            "Treat decode-then-execute as malicious until proven otherwise; "
            "legitimate code does not run decoded blobs."
        ),
    ),
    "sensitive_file_read": _SemgrepRuleMeta(
        rule_id="extrace.sg.sensitive_file_read",
        categories=("attack.T1552", "extrace.ext.credential_access"),
        title="Reference to a sensitive credential file path",
        description=(
            "The extension references a sensitive credential file path (SSH "
            "keys, cloud credentials, npmrc, or docker config), a common target "
            "for credential theft."
        ),
        mitigation_hint=(
            "Confirm why the extension touches credential stores; reading SSH / "
            "cloud credential files is a credential-access red flag."
        ),
    ),
    "reverse_shell_pipe": _SemgrepRuleMeta(
        rule_id="extrace.sg.reverse_shell_pipe",
        categories=("attack.T1059", "extrace.ext.reverse_shell"),
        title="Shell process stdio piped to a network socket",
        description=(
            "The extension pipes a child_process shell's stdio to a network "
            "socket (socket->stdin and/or stdout/stderr->socket). This "
            "bidirectional wiring is the defining structure of an interactive "
            "reverse shell. The in-house extrace.s10.reverse_shell rule carries "
            "the blocking verdict; this is the structural Semgrep echo."
        ),
        mitigation_hint=(
            "A shell process wired to a socket is a reverse shell — there is no "
            "legitimate extension use; reject it and block the endpoint."
        ),
    ),
    "reverse_shell_spawn": _SemgrepRuleMeta(
        rule_id="extrace.sg.reverse_shell_spawn",
        categories=("attack.T1059", "extrace.ext.process_spawn"),
        title="child_process spawn of an OS shell binary",
        description=(
            "The extension spawns an OS shell (cmd.exe / powershell / sh / bash) "
            "via child_process — the command interpreter a reverse shell hands "
            "to its socket. A shell-name-filtered refinement of the broader "
            "child_process rule."
        ),
        mitigation_hint=(
            "Confirm why the extension spawns a shell; a shell spawn paired with "
            "a network socket is the reverse-shell shape."
        ),
    ),
    "reverse_shell_ip_connect": _SemgrepRuleMeta(
        rule_id="extrace.sg.reverse_shell_ip_connect",
        categories=("attack.T1571", "extrace.ext.ip_connect"),
        title="Socket connect to a hardcoded IPv4 literal",
        description=(
            "The extension opens a socket to a hardcoded IPv4 literal with no "
            "DNS lookup. A real extension talks to named services, so a raw-IP "
            "callback target is a classic command-and-control / reverse-shell "
            "shape."
        ),
        mitigation_hint=(
            "Confirm why the extension connects to a raw IP; legitimate "
            "extensions use named services. Block the destination."
        ),
    ),
    "download_cradle": _SemgrepRuleMeta(
        rule_id="extrace.sg.download_cradle",
        categories=("attack.T1059", "attack.T1105", "extrace.ext.download_cradle"),
        title="PowerShell remote download cradle (dropper)",
        description=(
            "The extension contains a hidden-PowerShell download cradle "
            "(powershell -> Invoke-RestMethod / Invoke-WebRequest -> "
            "Invoke-Expression): it fetches a remote script and runs it in "
            "memory, the fetch-then-execute payload mechanism of a downloader / "
            "dropper. The in-house extrace.s11.download_cradle rule carries the "
            "blocking verdict; this is the cleartext-string echo that fires even "
            "under string-array obfuscation."
        ),
        mitigation_hint=(
            "Treat a fetch-and-execute PowerShell cradle as a dropper — there is "
            "no legitimate extension use; reject it and block the staging "
            "endpoint."
        ),
    ),
    "permissive_cors": _SemgrepRuleMeta(
        rule_id="extrace.sg.permissive_cors",
        categories=("attack.T1083", "extrace.ext.permissive_cors"),
        title="Permissive CORS on a server",
        description=(
            "The extension sets Access-Control-Allow-Origin to '*', exposing its "
            "server to any web origin. On a local file-serving extension server "
            "this is the reachable-origin half of a path-traversal vulnerability: "
            "a malicious page the developer opens can reach the server and, if a "
            "request path flows unguarded into a filesystem read, retrieve "
            "arbitrary local files. The in-house extrace.s15.path_traversal_server "
            "rule carries the full conjunction (server + unguarded request->read + "
            "reachable origin); this echoes the CORS surface alone at MEDIUM/WARN. "
            "This is a VULNERABILITY surface, not evidence of malice."
        ),
        mitigation_hint=(
            "Restrict the server's CORS policy to a known, specific origin instead "
            "of '*', and serve files through a hardened static library or an "
            "explicit path-containment check so the surface cannot be abused for "
            "path traversal."
        ),
    ),
    "cross_extension_write": _SemgrepRuleMeta(
        rule_id="extrace.sg.cross_extension_write",
        categories=("attack.T1554", "extrace.ext.cross_extension_tamper"),
        title="Filesystem write into a .vscode/extensions install path",
        description=(
            "The extension writes or copies a file into a .vscode/extensions "
            "install-root path — i.e. into another extension's install directory. "
            "VS Code performs no integrity check on installed extensions, so "
            "overwriting another extension's on-disk code makes it run attacker "
            "code on its next activation (local persistence / execution hijack). "
            "The in-house extrace.s16.cross_extension_tamper rule carries the "
            "blocking verdict (including the getExtension(other).extensionPath "
            "form); this is the install-root-literal echo."
        ),
        mitigation_hint=(
            "An extension has no legitimate reason to write into another "
            "extension's install directory — treat it as a tamper / persistence "
            "attempt, reject it, and verify the targeted extension's integrity."
        ),
    ),
    "home_dir_enumeration": _SemgrepRuleMeta(
        rule_id="extrace.sg.home_dir_enumeration",
        categories=("attack.T1083", "extrace.ext.host_recon"),
        title="Home-directory enumeration",
        description=(
            "The extension lists the user's home directory (fs.readdir over "
            "os.homedir()). Enumerating the home directory is a host-"
            "reconnaissance step that typically precedes credential / secret "
            "discovery and is rarely needed by a legitimate extension."
        ),
        mitigation_hint=(
            "Confirm why the extension enumerates the user's home directory; "
            "scanning $HOME is a discovery step ahead of credential theft."
        ),
    ),
    "device_fingerprint": _SemgrepRuleMeta(
        rule_id="extrace.sg.device_fingerprint",
        categories=("attack.T1082", "extrace.ext.device_fingerprint"),
        title="Device fingerprint collection",
        description=(
            "The extension collects a stable host identifier (MAC address via the "
            "macaddress module, or os.networkInterfaces()). Device fingerprinting "
            "is a reconnaissance step commonly paired with outbound exfiltration to "
            "track or target the victim host."
        ),
        mitigation_hint=(
            "Confirm why the extension fingerprints the host; a device identifier "
            "collected alongside a network sink is an exfiltration / tracking "
            "signal."
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
    deep_scan_targets: tuple[str, ...] = (),
    deep_scan_target_cap_reached: bool = False,
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
    deadline = start + max(_MIN_WALL_TIMEOUT_S, wall_timeout_s)
    vsix_root = Path(vsix_dir)
    rules_loaded = _count_rules()
    version = _SEMGREP_VERSION

    base_status, results, errors = _invoke_semgrep(
        _build_argv(
            targets=(vsix_dir,),
            per_rule_timeout_s=per_rule_timeout_s,
            exclude_inventory_only=True,
        ),
        timeout_s=max(_MIN_WALL_TIMEOUT_S, wall_timeout_s),
    )
    if base_status == "timeout":
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="timeout"
        )
    if base_status == "error":
        return _failure_result(
            version=version, rules_loaded=rules_loaded, start=start, status="error"
        )

    deep_status: _ToolStatus | None = None
    deep_budget_stopped = False
    if deep_scan_targets:
        remaining = int(deadline - time.monotonic())
        if remaining < _MIN_WALL_TIMEOUT_S:
            deep_budget_stopped = True
        else:
            deep_status, deep_results, deep_errors = _invoke_semgrep(
                _build_argv(
                    targets=deep_scan_targets,
                    per_rule_timeout_s=per_rule_timeout_s,
                    exclude_inventory_only=False,
                ),
                timeout_s=remaining,
            )
            if deep_status is None:
                results.extend(deep_results)
                errors.extend(deep_errors)

    findings: list[StaticDetectionFinding] = []
    finding_fingerprints: set[tuple[str, str, str, str, int, str]] = set()
    for raw in results:
        if len(findings) >= _MAX_FINDINGS:
            break
        finding = _map_result_to_finding(raw, vsix_root)
        if finding is not None:
            fingerprint = _finding_fingerprint(finding)
            if fingerprint in finding_fingerprints:
                continue
            finding_fingerprints.add(fingerprint)
            findings.append(finding)

    duration_ms = int((time.monotonic() - start) * 1000)
    coverage = _build_semgrep_coverage(
        vsix_root,
        raw_result_count=len(results),
        error_count=len(errors),
        deep_scan_targets=deep_scan_targets,
        deep_scan_skip_reason=(
            "budget_stop"
            if deep_budget_stopped
            else "tool_timeout"
            if deep_status == "timeout"
            else "tool_error"
            if deep_status == "error"
            else None
        ),
        deep_scan_target_cap_reached=deep_scan_target_cap_reached,
    )
    extra_reasons = set(coverage.coverage_reasons)
    if deep_budget_stopped:
        extra_reasons.add("budget_stop")
    if deep_status == "timeout":
        extra_reasons.add("tool_timeout")
    elif deep_status == "error":
        extra_reasons.add("tool_error")
    coverage.coverage_reasons = sorted(extra_reasons)
    record = StaticToolExecutionRecord(
        tool="semgrep",
        version=version,
        rules_loaded=rules_loaded,
        findings_emitted=len(findings),
        duration_ms=duration_ms,
        # Per-file parse errors / rule timeouts mean incomplete coverage — mark
        # the run partial (and surface the count) without failing it.
        status=(
            "partial"
            if (errors or coverage.coverage_reasons or deep_status is not None)
            else "ok"
        ),
        error_count=len(errors),
        errored_rule_ids=_collect_error_rule_ids(errors),
        coverage=coverage,
    )
    return SemgrepRunResult(findings=findings, record=record)


def _build_argv(
    *,
    targets: tuple[str, ...],
    per_rule_timeout_s: int,
    exclude_inventory_only: bool,
) -> list[str]:
    argv = [
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
    ]
    if exclude_inventory_only:
        for pattern in _BASE_EXCLUDED_PATTERNS:
            argv.extend(["--exclude", pattern])
    argv.extend(targets)
    return argv


def _invoke_semgrep(
    argv: list[str], *, timeout_s: int
) -> tuple[_ToolStatus | None, list[dict], list[dict]]:
    try:
        completed = subprocess.run(  # noqa: S603  # nosec B603
            argv,
            capture_output=True,
            text=True,
            timeout=max(_MIN_WALL_TIMEOUT_S, timeout_s),
            env=_build_env(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout", [], []
    except OSError:
        return "error", [], []
    if completed.returncode not in _SEMGREP_OK_RETURNCODES:
        return "error", [], []
    try:
        results, errors = _parse_results(completed.stdout)
    except (json.JSONDecodeError, ValueError):
        return "error", [], []
    return None, results, errors


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


def _finding_fingerprint(
    finding: StaticDetectionFinding,
) -> tuple[str, str, str, str, int, str]:
    """Return the canonical SMF-shaped fingerprint for a mapped finding."""

    evidence = finding.evidence[0] if finding.evidence else None
    snippet = evidence.snippet if evidence is not None else ""
    match_shape = hashlib.sha256((snippet or "").encode("utf-8")).hexdigest()[:16]
    return (
        finding.rule_id,
        finding.rule_version,
        evidence.relative_path if evidence is not None else "<report>",
        evidence.type if evidence is not None else "none",
        evidence.line_number if evidence is not None and evidence.line_number else 0,
        match_shape,
    )


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


def _build_semgrep_coverage(
    root: Path,
    *,
    raw_result_count: int,
    error_count: int,
    deep_scan_targets: tuple[str, ...] = (),
    deep_scan_skip_reason: StaticCoverageReason | None = None,
    deep_scan_target_cap_reached: bool = False,
) -> StaticScanCoverage:
    """Build bounded target accounting from Semgrep's deterministic selection policy."""

    discovered = 0
    eligible = 0
    scanned = 0
    bytes_considered = 0
    bytes_read = 0
    skipped: dict[str, int] = {}
    skipped_path_details: dict[str, list[str]] = {}
    unsupported: dict[str, int] = {}
    deep_relative_paths: set[str] = set()
    for target in deep_scan_targets:
        try:
            deep_relative_paths.add(Path(target).relative_to(root).as_posix())
        except ValueError:
            continue
    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            discovered += 1
            relative = path.relative_to(root)
            suffix = path.suffix.lower() or "<none>"
            relative_posix = relative.as_posix()
            inventory_excluded = is_vendor_path(relative_posix) or is_minified_path(
                relative_posix
            )
            if inventory_excluded and relative_posix not in deep_relative_paths:
                skipped["excluded_inventory_only"] = (
                    skipped.get("excluded_inventory_only", 0) + 1
                )
                skipped_path_details.setdefault("excluded_inventory_only", []).append(
                    relative.as_posix()
                )
                continue
            if suffix not in _SEMGREP_SOURCE_SUFFIXES:
                unsupported[suffix] = unsupported.get(suffix, 0) + 1
                continue
            eligible += 1
            if relative_posix in deep_relative_paths and deep_scan_skip_reason:
                skipped[deep_scan_skip_reason] = (
                    skipped.get(deep_scan_skip_reason, 0) + 1
                )
                skipped_path_details.setdefault(deep_scan_skip_reason, []).append(
                    relative_posix
                )
                continue
            try:
                size = path.stat().st_size
            except OSError:
                skipped["parser_error"] = skipped.get("parser_error", 0) + 1
                skipped_path_details.setdefault("parser_error", []).append(
                    relative.as_posix()
                )
                continue
            bytes_considered += size
            if size > _MAX_TARGET_BYTES:
                skipped["target_too_large"] = skipped.get("target_too_large", 0) + 1
                skipped_path_details.setdefault("target_too_large", []).append(
                    relative.as_posix()
                )
                continue
            scanned += 1
            bytes_read += size

    reasons: list[StaticCoverageReason] = []
    if skipped.get("target_too_large"):
        reasons.append("target_too_large")
    if skipped.get("parser_error") or error_count:
        reasons.append("parser_error")
    if skipped.get("budget_stop"):
        reasons.append("budget_stop")
    if skipped.get("tool_timeout"):
        reasons.append("tool_timeout")
    if skipped.get("tool_error"):
        reasons.append("tool_error")
    if deep_scan_target_cap_reached:
        reasons.append("deep_scan_target_cap")
    finding_cap_reached = raw_result_count > _MAX_FINDINGS
    if finding_cap_reached:
        reasons.append("finding_cap")
        skipped["finding_cap"] = raw_result_count - _MAX_FINDINGS
    # Intentional scope exclusions remain visible in the inventory accounting,
    # but are not a degraded execution state. The in-house production rules scan
    # these text files; Semgrep's advisory echo rules exclude vendor/minified
    # trees to keep parser cost and duplicate noise bounded. Real loss conditions
    # (oversize targets, parse errors, caps) still populate ``coverage_reasons``.

    return StaticScanCoverage(
        files_discovered=discovered,
        files_selected=eligible,
        files_eligible=eligible,
        files_scanned=scanned,
        files_parsed=scanned,
        files_skipped_by_reason=skipped,
        skipped_paths_by_reason={
            reason: sorted(set(paths))[:_MAX_PATH_DETAILS]
            for reason, paths in skipped_path_details.items()
        },
        bytes_considered=bytes_considered,
        bytes_read=bytes_read,
        finding_cap_reached=finding_cap_reached,
        unsupported_formats=unsupported,
        coverage_reasons=reasons,
    )


def get_semgrep_rule_inventory() -> tuple[SemgrepRuleInventoryEntry, ...]:
    """Return deterministic metadata for every mappable Semgrep rule.

    The inventory deliberately comes from the same mapping table used to build
    production findings. This prevents the measurement baseline from silently
    drifting away from the rules the runner can actually emit.
    """

    return tuple(
        SemgrepRuleInventoryEntry(
            rule_id=meta.rule_id,
            rule_version=_RULE_VERSION,
            rule_lifecycle=RuleLifecycle.PRODUCTION.value,
            severity=Severity.MEDIUM.value,
            confidence=Confidence.MEDIUM.value,
            categories=meta.categories,
            capabilities=(meta.rule_id.rsplit(".", 1)[-1],),
            gate_effect="warn",
            artifact_roles=("source_file",),
            test_ownership=("tests/security/test_semgrep_js_rules.py",),
            positive_tests=("tests/security/test_semgrep_js_rules.py",),
            negative_tests=("tests/security/test_semgrep_js_rules.py",),
            known_false_positives=(
                "Syntactic advisory matches can lack source-to-sink context.",
            ),
            known_blind_spots=(
                "Semgrep excludes vendor/minified sources, targets above 32 MiB, "
                "and unsupported languages; in-house rules retain bounded "
                "text coverage.",
            ),
            runtime_budget=(
                f"32 MiB per target; {_SEMGREP_PER_RULE_TIMEOUT_S}s per rule/file; "
                "outer static-analysis wall clock"
            ),
            owner="security-detection",
        )
        for meta in sorted(_RULE_META.values(), key=lambda item: item.rule_id)
    )


def get_semgrep_rule_source_digests() -> tuple[tuple[str, str], ...]:
    """Return relative names and SHA-256 digests of the exact shipped YAML bytes."""

    return tuple(
        (
            rule_path.relative_to(_RULES_DIR).as_posix(),
            hashlib.sha256(rule_path.read_bytes()).hexdigest(),
        )
        for rule_path in sorted(_RULES_DIR.rglob("*.yml"))
    )


def get_semgrep_version() -> str:
    """Return the exact pinned Semgrep version recorded by production runs."""

    return _SEMGREP_VERSION


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
            coverage=StaticScanCoverage(
                coverage_reasons=[
                    "tool_timeout" if status == "timeout" else "tool_error"
                ]
            ),
        ),
    )


__all__ = [
    "SemgrepRuleInventoryEntry",
    "SemgrepRunResult",
    "get_semgrep_rule_inventory",
    "get_semgrep_rule_source_digests",
    "get_semgrep_version",
    "run_semgrep",
]
