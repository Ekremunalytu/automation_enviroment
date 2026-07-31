"""S10 static rule: child_process shell stdio wired to a network socket.

Detects the *reverse-shell signature* (RS1): inside one bounded source region, a
``child_process`` shell spawn and raw network socket are connected by identifier,
and a **bidirectional pipe** wires the spawned shell's stdio to that socket. The
connected conjunction is
what makes an interactive reverse shell — the attacker writes to the socket, the
bytes land on the victim's shell stdin, and the shell's stdout/stderr stream back
out. See ``documents/detection-design/securezeron-detection-spec.md`` (signal RS1).

The rule keys on the **connected conjunction**, never file-wide parts.
``child_process`` alone is benign (extensions shell out to git / build tools /
language servers); a socket
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
    line_number_at,
    snippet_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 9
_MAX_CHAIN_SPAN = 8 * 1024

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

# Process/socket assignments anchor the identifiers used by both bridge legs.
_PROCESS_ASSIGN_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
    r"(?:[A-Za-z_$][\w$]*\s*\.\s*)?"
    r"(?:execFileSync|execFile|execSync|exec|spawnSync|spawn)\s*\([^;{}]{0,400}\)"
)
_SOCKET_ASSIGN_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
    r"(?:new\s+)?(?:[A-Za-z_$][\w$]*\s*\.\s*)?"
    r"(?:Socket|connect|createConnection)\s*\("
)


class ReverseShellRule:
    rule_id = "extrace.s10.reverse_shell"
    rule_version = "1.1.0"
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
            chain = self._connected_chain(text)
            if chain is not None:
                return [self._finding(context, relative_path, text, chain)]

        return []

    @staticmethod
    def _connected_chain(
        text: str,
    ) -> tuple[re.Match[str], re.Match[str], re.Match[str], re.Match[str]] | None:
        """Return a variable-connected, bidirectional shell/socket bridge."""

        for process in _PROCESS_ASSIGN_RE.finditer(text):
            process_name = process.group(1)
            # Only socket assignments close enough to satisfy the final chain
            # bound can contribute. Re-scanning an entire production bundle for
            # every process assignment made this rule quadratic on minified
            # sources and could consume the static runner's whole 30s budget.
            socket_search_start = max(0, process.end() - _MAX_CHAIN_SPAN)
            socket_search_end = min(len(text), process.start() + _MAX_CHAIN_SPAN)
            for socket in _SOCKET_ASSIGN_RE.finditer(
                text, socket_search_start, socket_search_end
            ):
                socket_name = socket.group(1)
                start = min(process.start(), socket.start())
                end = max(process.end(), socket.end())
                if end - start > _MAX_CHAIN_SPAN:
                    continue
                region_start = max(0, start - _MAX_CHAIN_SPAN)
                region_end = min(len(text), end + _MAX_CHAIN_SPAN)
                region = text[region_start:region_end]
                inbound_pattern = re.compile(
                    rf"\b{re.escape(socket_name)}\s*\.\s*pipe\s*\(\s*"
                    rf"{re.escape(process_name)}\s*\.\s*stdin\b"
                    rf"|\b{re.escape(process_name)}\s*\.\s*stdin\s*\.\s*write\s*\("
                )
                outbound_pattern = re.compile(
                    rf"\b{re.escape(process_name)}\s*\.\s*std(?:out|err)\s*"
                    rf"\.\s*pipe\s*\(\s*{re.escape(socket_name)}\b"
                    rf"|\b{re.escape(process_name)}\s*\.\s*std(?:out|err)\s*"
                    rf"\.\s*on\s*\([\s\S]{{0,400}}?\b{re.escape(socket_name)}\s*"
                    rf"\.\s*write\s*\("
                )
                for inbound in inbound_pattern.finditer(region):
                    inbound_abs = inbound_pattern.search(
                        text,
                        region_start + inbound.start(),
                        region_start + inbound.end(),
                    )
                    if inbound_abs is None:
                        continue
                    for outbound in outbound_pattern.finditer(region):
                        outbound_abs = outbound_pattern.search(
                            text,
                            region_start + outbound.start(),
                            region_start + outbound.end(),
                        )
                        if outbound_abs is None:
                            continue
                        chain = (process, socket, inbound_abs, outbound_abs)
                        chain_start = min(match.start() for match in chain)
                        chain_end = max(match.end() for match in chain)
                        if chain_end - chain_start > _MAX_CHAIN_SPAN:
                            continue
                        shell_start = max(0, chain_end - _MAX_CHAIN_SPAN)
                        shell_end = min(len(text), chain_start + _MAX_CHAIN_SPAN)
                        if any(
                            max(chain_end, shell.end())
                            - min(chain_start, shell.start())
                            <= _MAX_CHAIN_SPAN
                            for shell in _SHELL_NAME_RE.finditer(
                                text, shell_start, shell_end
                            )
                        ):
                            return chain
        return None

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        chain: tuple[re.Match[str], re.Match[str], re.Match[str], re.Match[str]],
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        for match in chain:
            self._add_match(evidence, context, relative_path, text, match)

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
                "(shell spawn, socket, stdio<->socket pipe), the same process/socket "
                "identifiers, and both bridge directions in a bounded code region, "
                "so unrelated bundled libraries do not fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat a shell process piped to a network socket as a reverse "
                "shell — there is no legitimate reason for an extension to do "
                "this. Reject the extension and block the remote endpoint."
            ),
        )

    @staticmethod
    def _add_match(
        evidence: list[StaticEvidenceRef],
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        match: re.Match[str],
    ) -> None:
        if len(evidence) >= _MAX_EVIDENCE:
            return
        line_number = line_number_at(text, match.start())
        evidence.append(
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=snippet_at(text, match.start()) or "reverse-shell wiring",
                line_number=line_number,
            )
        )


register(ReverseShellRule())

__all__ = ["ReverseShellRule"]
