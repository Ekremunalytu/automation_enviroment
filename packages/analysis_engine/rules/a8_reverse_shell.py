"""A8 detection rule: runtime reverse shell (shell spawn + outbound socket).

The runtime counterpart of the static ``extrace.s10.reverse_shell`` rule. The
static rule reads the stdio<->socket *wiring* out of the source; the sandbox does
not see that wiring, but it does see the two observable halves: the target
extension spawns an OS **shell** process (a ``kind="process"`` strace event whose
command is sh / bash / cmd.exe / powershell) and opens an **outbound socket** to a
non-benign endpoint, close together after activation. That co-occurrence is the
runtime signature of a reverse shell.

It is HIGH / MEDIUM-confidence, not CRITICAL: the file layer proves the wiring and
blocks pre-sandbox (``s10``); here the sandbox observes spawn + egress but not the
pipe between them, so a benign extension that both shells out (a build task) and
beacons could in principle co-occur. The shell-binary filter is the false-positive
guard — a language server / debugger / git spawn (node, python, git) is not a
shell and does not enter the correlation. ``adversary_class = A8``.
"""

from __future__ import annotations

import re

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import (
    is_target_owned,
    make_evidence_ref,
    rel_time,
    target_unknown_outbound_network_events,
)
from packages.analysis_engine.rules.registry import register

# How far apart the shell spawn and the outbound socket may sit and still be read
# as one reverse-shell action (seconds, either order: the socket may be created
# just before the shell is spawned, or just after).
_CORRELATION_WINDOW_S = 30.0

# An OS command interpreter as a process command/binary. Bounded by a path
# separator or whitespace so a substring (``dashboard``, ``bash-completion``)
# does not match; ``node`` / ``python`` / ``git`` deliberately do not.
_SHELL_BINARY_RE = re.compile(
    r"(?:^|[/\\\s])(?:sh|bash|dash|zsh|ksh|cmd|powershell|pwsh)(?:\.exe)?(?:$|\s)",
    re.IGNORECASE,
)


def _process_command(event: EvidenceEvent) -> str:
    # Only the ProcessRawContext variant carries ``command``; other variants
    # return "" via getattr's default (the _common event_* reader pattern).
    return str(getattr(event.raw_context, "command", "")).strip()


def _target_shell_spawns(report: ActivationReport) -> list[EvidenceEvent]:
    return [
        event
        for event in report.evidence_events
        if event.kind == "process"
        and is_target_owned(event)
        and _SHELL_BINARY_RE.search(_process_command(event))
    ]


class ReverseShellRule:
    rule_id = "extrace.a8.reverse_shell"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A8
    severity = Severity.HIGH
    description = "Shell spawn co-occurring with an outbound socket (reverse shell)."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        shell_spawns = _target_shell_spawns(report)
        if not shell_spawns:
            return []
        outbound_events = target_unknown_outbound_network_events(report)
        if not outbound_events:
            return []

        for spawn in shell_spawns:
            for network_event in outbound_events:
                delta = abs(rel_time(network_event) - rel_time(spawn))
                if delta <= _CORRELATION_WINDOW_S:
                    return [self._finding(spawn, network_event)]
        return []

    def _finding(
        self, spawn: EvidenceEvent, network_event: EvidenceEvent
    ) -> DetectionFinding:
        return DetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1059", "extrace.host.reverse_shell"],
            severity=self.severity,
            confidence=Confidence.MEDIUM,
            title="Shell spawn co-occurring with an outbound socket (reverse shell)",
            description=(
                "The extension spawned an OS shell and opened an outbound socket "
                "to a non-benign endpoint within "
                f"{int(_CORRELATION_WINDOW_S)}s. This is the runtime signature of "
                "an interactive reverse shell: a command interpreter bridged to a "
                "remote endpoint. The sandbox observes the shell spawn and the "
                "egress but not the stdio wiring between them, so this surfaces a "
                "strong correlation for review (the static s10 rule convicts on "
                "the wiring itself)."
            ),
            evidence=[
                make_evidence_ref(spawn),
                make_evidence_ref(network_event),
            ],
            adversary_class=self.adversary_class,
            mitigation_hint=(
                "Treat a shell spawn paired with an outbound socket as a reverse "
                "shell until proven otherwise; review the spawned command and "
                "block the observed destination."
            ),
        )


RULE = ReverseShellRule()
register(RULE)

__all__ = ["RULE", "ReverseShellRule"]
