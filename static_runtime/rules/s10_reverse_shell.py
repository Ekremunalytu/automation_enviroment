"""S10 static rule: child_process shell stdio wired to a network socket.

Detects the *reverse-shell signature* (RS1): inside one source file, a
``child_process`` shell spawn, a raw network socket, and a **bidirectional pipe**
that wires the spawned shell's stdio to that socket co-occur. That conjunction is
what makes an interactive reverse shell — the attacker writes to the socket, the
bytes land on the victim's shell stdin, and the shell's stdout/stderr stream back
out. See ``documents/detection-design/securezeron-detection-spec.md`` (signal RS1).

The rule keys on the **conjunction**, never the parts. ``child_process`` alone is
benign (extensions shell out to git / build tools / language servers); a socket
alone is benign (telemetry, update checks); a ``.pipe()`` alone is benign (stream
plumbing). It is the shell-stdio↔socket wiring that has no legitimate use in a VS
Code extension, so requiring all three in the same module collapses the false-
positive rate to near zero while still catching the platform-selected-shell shape
(``const shell = isWin ? "cmd.exe" : "sh"; child_process.exec(shell)``) where the
shell name and the spawn call sit on different lines.

Like ``s11`` (the download cradle) this one is **CRITICAL** (most static IOC rules,
e.g. ``s8``/``s9``, are HIGH/MEDIUM warns): a piped shell↔socket is not a capability
surface to review but a finished reverse shell, so it blocks at the static gate
before the sandbox runs (ADR 0016: CRITICAL -> BLOCK / ``rejected_static``; see the
architecture-reconciliation doc). ``adversary_class`` stays ``None``: like every
in-house static rule it reports a *capability/IOC surface*; runtime attribution
(the shell-spawn + outbound-socket correlation) belongs to the dynamic plane. The
rule logic is general-purpose (no sample literal); the securezeron IOCs live only
in tests + the spec appendix.
"""

from __future__ import annotations

import re

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import (
    evidence_type_for,
    file_evidence,
    iter_text_documents,
    line_at,
    line_number_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 9

# A child_process spawn primitive or an import of the module itself. ``fork`` is
# excluded (it spawns a Node child, not an OS shell) so a worker-thread pattern
# does not enter the conjunction.
_CHILD_PROCESS_RE = re.compile(
    r"child_process"
    r"|\b(?:execFileSync|execFile|execSync|exec|spawnSync|spawn)\s*\("
)

# A shell binary referenced anywhere in the file — matched separately from the
# spawn call so the platform-selected-shell idiom (shell name assigned to a
# variable, spawned later) is still caught. ``\bsh\b`` is broad on its own, but
# it only contributes inside the three-way conjunction, so it cannot fire alone.
_SHELL_NAME_RE = re.compile(
    r"cmd\.exe"
    r"|powershell(?:\.exe)?"
    r"|/bin/(?:ba)?sh"
    r"|\bbash\b"
    r"|\bsh\b"
    r"|ComSpec"
    r"|process\.env\.SHELL",
    re.IGNORECASE,
)

# A raw outbound socket capability (``net`` clear / ``tls`` encrypted). Covers the
# evasion note in the spec: a reverse shell that swaps ``net.Socket`` for
# ``tls.connect`` still trips this conjunct.
_SOCKET_RE = re.compile(
    r"net\.(?:Socket|connect|createConnection)\b"
    r"|tls\.connect\b"
    r"|require\(\s*['\"](?:node:)?(?:net|tls)['\"]\s*\)"
)

# The load-bearing conjunct: a ``.pipe()`` that wires a process stdio stream to a
# socket, in either direction —
#   * ``proc.stdout.pipe(socket)`` / ``proc.stderr.pipe(socket)``  (shell -> C2)
#   * ``socket.pipe(proc.stdin)``                                   (C2 -> shell)
_PIPE_WIRING_RE = re.compile(
    r"\.std(?:out|err)\s*\.pipe\s*\("
    r"|\.pipe\s*\(\s*[\w.]*\bstdin\b"
)


class ReverseShellRule:
    rule_id = "extrace.s10.reverse_shell"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # CRITICAL -> BLOCK before the sandbox: a shell whose stdio is piped to a
    # network socket has no benign explanation; it is convicted on the static
    # conjunction alone (the only severity-CRITICAL in-house rule).
    severity = Severity.CRITICAL
    description = (
        "Extension source wires a child_process shell's stdio to a network "
        "socket (bidirectional pipe), the defining signature of an interactive "
        "reverse shell."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            has_child_process = _CHILD_PROCESS_RE.search(text) is not None
            has_shell_name = _SHELL_NAME_RE.search(text) is not None
            has_socket = _SOCKET_RE.search(text) is not None
            has_pipe_wiring = _PIPE_WIRING_RE.search(text) is not None

            if not (
                has_child_process and has_shell_name and has_socket and has_pipe_wiring
            ):
                continue

            return [self._finding(context, relative_path, text)]

        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        for pattern in (_PIPE_WIRING_RE, _CHILD_PROCESS_RE, _SOCKET_RE):
            self._add_first_match(evidence, context, relative_path, text, pattern)

        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1059", "extrace.ext.reverse_shell"],
            severity=self.severity,
            confidence=Confidence.HIGH,
            title="Extension wires a shell process to a network socket (reverse shell)",
            description=(
                "The extension source spawns an OS shell via child_process and "
                "pipes that shell's stdio to a raw network socket. This "
                "bidirectional wiring of shell input/output to a socket is the "
                "defining structure of an interactive reverse shell: it grants a "
                "remote endpoint a live command channel on the victim host with no "
                "user interaction. The match requires all three elements "
                "(shell spawn, socket, stdio<->socket pipe) in one file, so the "
                "individual benign uses of child_process or sockets do not fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat a shell process piped to a network socket as a reverse "
                "shell — there is no legitimate reason for an extension to do "
                "this. Reject the extension and block the remote endpoint."
            ),
        )

    @staticmethod
    def _add_first_match(
        evidence: list[StaticEvidenceRef],
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        pattern: re.Pattern[str],
    ) -> None:
        if len(evidence) >= _MAX_EVIDENCE:
            return
        match = pattern.search(text)
        if match is None:
            return
        line_number = line_number_at(text, match.start())
        evidence.append(
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=line_at(text, line_number) or "reverse-shell wiring",
                line_number=line_number,
            )
        )


register(ReverseShellRule())

__all__ = ["ReverseShellRule"]
