"""S11 static rule: child_process driving a PowerShell remote download cradle.

Detects the *dropper / download-cradle signature* (DR5): inside one source file a
``child_process`` shell-exec sink co-occurs with a hidden-PowerShell **download
cradle** — ``powershell ... irm|iwr|Invoke-RestMethod|Invoke-WebRequest <url> ...
iex|Invoke-Expression`` — i.e. fetch-remote-then-execute-in-memory. That cradle
is the kagema / ``ShowSnowcrypto.SnowShoNo`` family's payload mechanism: the
extension spawns a hidden PowerShell that pulls a second stage off the network and
runs it filelessly (``| iex``), with no user interaction. See
``documents/detection-design/kagema-detection-spec.md`` (signal DR5, the detection
invariant).

The rule keys on the **conjunction**, never the parts. ``child_process`` alone is
benign (extensions shell out to git / build tools / language servers); a bare
``powershell`` mention is benign; an ``iex`` token alone is benign. It is the
*ordered cradle shape* — ``powershell`` then a download verb then an in-memory
execute verb, within one bounded span — wired to a ``child_process`` sink that has
no legitimate use in a VS Code extension. The cradle is matched as a single
bounded, ordered regex rather than four independent file-level tokens on purpose:
the loose four-token co-occurrence false-positives on large benign bundles (it
trips ``GitHub.copilot-chat``'s ``dist/cli.js``), whereas the ordered single-span
shape is zero-FP across the benign corpus. The trade-off is documented in the
spec §4: an APT variant that splits the command across lines / concatenation
(``+`` / here-string) evades this single-span match and is left to the dynamic
plane.

Like ``s10`` this is **CRITICAL** and blocks at the static gate before the sandbox
runs (ADR 0016: CRITICAL -> BLOCK / ``rejected_static``). A hidden-PowerShell
fetch-and-execute cradle is not a capability surface to review but a finished
remote-code-execution primitive. Blocking here is load-bearing for *this* family
specifically: the payload is gated on ``process.platform === "win32"``, so a
Linux-based dynamic sandbox never fires it (spec §6) — the static layer is the
only one that observes the cradle, so it must convict. ``adversary_class`` stays
``None`` per the static-IOC convention (architecture-reconciliation doc: in-house
static rules report a capability/IOC surface; adversary-class attribution belongs
to the dynamic a-rules). The conceptual class is **A4** (Remote-loader dropper,
ADR 0002), documented in the kagema spec §7 — kept there rather than on a firing
rule because for this win32-gated family the dynamic plane that would normally
carry A4 is blind.
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

# A child_process shell-exec sink: an import of the module, or a bare spawn/exec
# primitive. ``fork`` is excluded (it spawns a Node child, not an OS shell).
# Identical to s10's sink conjunct so the dropper and reverse-shell rules agree on
# what "shells out" means.
_CHILD_PROCESS_RE = re.compile(
    r"child_process"
    r"|\b(?:execFileSync|execFile|execSync|exec|spawnSync|spawn)\s*\("
)

# The download cradle, matched as ONE ordered, bounded, single-line span:
#   powershell|pwsh ... irm|iwr|Invoke-RestMethod|Invoke-WebRequest
#   ... iex|Invoke-Expression
# ``[^\n]{0,200}`` keeps it on one logical line and bounds the gap so scattered
# tokens across a large file do not assemble into a false match. Plaintext under
# javascript-obfuscator string-array obfuscation too: that obfuscator renames
# identifiers but leaves string literals (the command) in cleartext, so the cradle
# survives in the literal pool (spec §4). The download-verb set is deliberately
# the proven zero-FP set; LOLBin diversification (mshta / rundll32 / certutil /
# bitsadmin) and curl/wget aliases are a documented evasion gap (spec §7).
_CRADLE_RE = re.compile(
    r"(?:powershell|pwsh)\b[^\n]{0,200}"
    r"\b(?:irm|iwr|invoke-restmethod|invoke-webrequest)\b[^\n]{0,200}"
    r"\b(?:iex|invoke-expression)\b",
    re.IGNORECASE,
)


class DownloadCradleRule:
    rule_id = "extrace.s11.download_cradle"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    # Class-less per the static-IOC convention (reconciliation doc): in-house
    # static rules report a capability/IOC surface and leave adversary-class
    # attribution to the dynamic a-rules. A4 (Remote-loader dropper) is the
    # conceptual class, documented in the kagema spec §7 — the dynamic plane that
    # would carry it is win32-blind for this family.
    adversary_class: AdversaryClass | None = None
    # CRITICAL -> BLOCK before the sandbox: a hidden-PowerShell fetch-and-execute
    # cradle is a finished RCE primitive with no benign explanation, and for this
    # win32-gated family the Linux sandbox never fires it, so static must convict.
    severity = Severity.CRITICAL
    description = (
        "Extension source drives a child_process sink with a hidden-PowerShell "
        "remote download cradle (irm/iwr -> iex), the fetch-then-execute payload "
        "mechanism of a downloader/dropper."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            has_child_process = _CHILD_PROCESS_RE.search(text) is not None
            has_cradle = _CRADLE_RE.search(text) is not None
            if not (has_child_process and has_cradle):
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
        # Cradle line first (the load-bearing evidence), then the sink.
        for pattern in (_CRADLE_RE, _CHILD_PROCESS_RE):
            self._add_first_match(evidence, context, relative_path, text, pattern)

        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1059", "attack.T1105", "extrace.ext.download_cradle"],
            severity=self.severity,
            confidence=Confidence.HIGH,
            title="Extension runs a PowerShell remote download cradle (dropper)",
            description=(
                "The extension source spawns a process via child_process and runs a "
                "hidden PowerShell download cradle: it fetches a remote script "
                "(Invoke-RestMethod / Invoke-WebRequest) and executes it in memory "
                "(Invoke-Expression / iex), downloading and running an arbitrary "
                "second stage on the host with no user interaction and nothing "
                "written to disk. The match requires the child_process sink and the "
                "ordered powershell->download->execute cradle in one file, so the "
                "individually benign uses of child_process or a PowerShell mention "
                "do not fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat a hidden-PowerShell fetch-and-execute cradle as a dropper — "
                "there is no legitimate reason for an extension to download and run "
                "a remote script in memory. Reject the extension and block the "
                "staging endpoint."
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
                snippet=line_at(text, line_number) or "download cradle",
                line_number=line_number,
            )
        )


register(DownloadCradleRule())

__all__ = ["DownloadCradleRule"]
