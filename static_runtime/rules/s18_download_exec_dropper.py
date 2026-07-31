"""S18 static rule: a file is made executable (``chmod +x``) and then run —
the drop-and-run primitive of a dropper / loader (ecm3401 DROP1).

The ecm3401 "Educational Attack Suite" ships ``func_download_script``: fetch a
remote script, ``createWriteStream`` it to disk, ``chmod +x`` it, then
``spawn(file, {detached:true})``. That is the textbook **ingress-tool-transfer +
execute** chain (MITRE T1105 + T1059). See
``documents/detection-design/ecm3401-malicious-suite-spec.md`` (signal DROP1).

A pure Semgrep taint cannot connect the downloaded bytes to the spawn, because the
bytes flow through ``createWriteStream(filename)`` (a stream, not a value) and
``filename`` is a separate literal — the dataflow is broken (spec §4c). The
**catchable invariant** the spec identifies is therefore the drop-and-run core:
*a file is given the executable bit and then executed*. This rule keys on the
conjunction of

  (A) a "make executable" operation — a shell ``chmod ... +x`` command, or an
      ``fs.chmod``/``chmodSync`` with an executable mode (owner/group/other exec
      bit set), and
  (B) a process-execution sink (``child_process`` ``spawn`` / ``exec`` /
      ``execFile`` and their ``*Sync`` forms),

in one source file. Making a file executable has essentially no purpose other than
to run it, so ``chmod +x`` immediately followed by an exec/spawn is the
drop-and-run signature.

Two confidence boosters refine the verdict without gating it:

  * **remote fetch present** (``fetch`` / ``http(s).get`` / ``axios`` /
    ``node-fetch``) — the full download->chmod->execute dropper chain, vs. a
    locally-staged binary;
  * **shared symbol** — the same identifier is the ``chmod +x`` target *and* the
    exec target (``chmod +x F`` ... ``spawn(F)``), which is the spec's
    highest-fidelity DROP1 sub-invariant.

When either holds, confidence is HIGH; otherwise MEDIUM.

Severity is **HIGH / WARN, not CRITICAL / BLOCK**. Unlike ``s11`` (a hidden
``powershell ... | iex`` fileless cradle, which has no benign use), drop-and-run
*does* have a legitimate cousin: a language-server / toolchain extension that
downloads a helper binary, ``chmod +x`` it, and runs it. Rejecting that before the
sandbox would be a trust-destroying false positive, so the finding surfaces the
ingress-tool-transfer + execute capability for review rather than convicting.
``adversary_class`` stays ``None`` per the static-IOC convention; A4 (remote-loader
dropper) is the conceptual class, carried at runtime (the dynamic plane observes
the ``execve`` of the dropped child — provided ``strace -f`` follows the fork,
the documented gap in spec §5). The known FN (spec §7): a dropper that executes
the payload through ``require``/``vm`` instead of ``child_process``, or fetches a
``.js`` it ``eval``s (no exec bit needed), slips this exec-bit-keyed match.
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
    find_local_pattern_cluster,
    iter_text_documents,
    line_number_at,
    snippet_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 9
_MAX_CHAIN_SPAN = 8 * 1024

# (A) "Make executable":
#   * a shell ``chmod ... +x`` command (the +x flag, on one logical line), or
#   * ``fs.chmod``/``chmodSync(target, <mode>)`` where the literal mode has an
#     execute bit — at least one octal digit in {1,3,5,7} (so 0o755/0o700/'744'
#     match; 0o644 / '600' do not). A non-literal/variable mode is not matched
#     (no false executable-bit claim).
_CHMOD_EXEC_RE = re.compile(
    r"chmod\b[^\n'\"`;]*\+x"
    r"|chmod(?:Sync)?\s*\([^;{}\n]*?,\s*(?:0o?[0-7]*[1357][0-7]*|['\"][0-7]*[1357][0-7]*['\"])"
)

# (B) A child_process execution sink. ``fork`` is excluded (it spawns a Node
# child, not an arbitrary executable).
_EXEC_SINK_RE = re.compile(
    r"\b(?:child_process\s*\.\s*)?"
    r"(?:spawnSync|spawn|execFileSync|execFile|execSync|exec)\s*\("
)

# Confidence booster: a remote fetch primitive (the download leg of the chain).
_REMOTE_FETCH_RE = re.compile(
    r"\bfetch\s*\("
    r"|\bhttps?\s*\.\s*(?:get|request)\s*\("
    r"|require\(\s*['\"](?:node-fetch|axios|got|undici)['\"]\s*\)"
    r"|\baxios\b"
)

# Symbol extractors for the shared-symbol booster. Each captures a leading
# identifier; ``${var}`` / quote / ``+`` glue before the identifier is skipped so
# ``chmod +x ${f}`` and ``spawn(f, ...)`` both yield ``f``.
_CHMOD_TARGET_RE = re.compile(
    r"chmod\b[^\n'\"`;]*\+x\s*['\"`]?\s*\+?\s*(?:\$\{)?\s*([A-Za-z_$][\w$]*)"
    r"|chmod(?:Sync)?\s*\(\s*(?:\$\{)?\s*([A-Za-z_$][\w$]*)"
)
_EXEC_TARGET_RE = re.compile(
    r"\b(?:spawnSync|spawn|execFileSync|execFile|execSync|exec)\s*\(\s*"
    r"(?:\$\{)?\s*([A-Za-z_$][\w$]*)"
)


class DownloadExecDropperRule:
    rule_id = "extrace.s18.download_exec_dropper"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # HIGH / WARN, not CRITICAL / BLOCK: drop-and-run has a legitimate cousin (a
    # toolchain/LSP extension downloading + running a helper binary), so this
    # surfaces the ingress-tool-transfer + execute capability for review.
    severity = Severity.HIGH
    description = (
        "Extension source makes a file executable (chmod +x) and runs it via "
        "child_process — the drop-and-run primitive of a downloader/dropper, "
        "especially when paired with a remote fetch."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            cluster = find_local_pattern_cluster(
                text,
                (_CHMOD_EXEC_RE, _EXEC_SINK_RE),
                max_span=_MAX_CHAIN_SPAN,
            )
            if cluster is None:
                continue
            start = max(0, min(match.start() for match in cluster) - 1024)
            end = min(len(text), max(match.end() for match in cluster) + 1024)
            region = text[start:end]
            fetch = _REMOTE_FETCH_RE.search(region)
            has_fetch = fetch is not None
            shared = self._shared_symbol(region)
            evidence_matches = list(cluster)
            if fetch is not None:
                absolute_fetch = _REMOTE_FETCH_RE.search(
                    text, start + fetch.start(), start + fetch.end()
                )
                if absolute_fetch is not None:
                    evidence_matches.append(absolute_fetch)
            return [
                self._finding(
                    context,
                    relative_path,
                    text,
                    evidence_matches=tuple(evidence_matches),
                    has_fetch=has_fetch,
                    shared=shared,
                )
            ]
        return []

    @staticmethod
    def _shared_symbol(text: str) -> bool:
        """True if a chmod-+x target identifier is also an exec/spawn target.

        ``chmod +x F`` ... ``spawn(F)`` with the same ``F`` is the spec's
        highest-fidelity DROP1 sub-invariant. Imperfect extraction degrades to
        ``False`` (the finding still fires at MEDIUM confidence).
        """
        chmod_targets = {
            group
            for match in _CHMOD_TARGET_RE.finditer(text)
            for group in match.groups()
            if group
        }
        if not chmod_targets:
            return False
        exec_targets = {match.group(1) for match in _EXEC_TARGET_RE.finditer(text)}
        return bool(chmod_targets & exec_targets)

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        *,
        evidence_matches: tuple[re.Match[str], ...],
        has_fetch: bool,
        shared: bool,
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        for match in evidence_matches:
            self._add_match(evidence, context, relative_path, text, match)

        confidence = Confidence.HIGH if (has_fetch or shared) else Confidence.MEDIUM
        chain = "download" if has_fetch else "staged"
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=[
                "attack.T1105",
                "attack.T1059",
                "extrace.ext.download_exec_dropper",
            ],
            severity=self.severity,
            confidence=confidence,
            title="Extension makes a file executable and runs it (dropper)",
            description=(
                "The extension source gives a file the executable bit (chmod +x or "
                "an fs.chmod with an exec mode) and then executes it via "
                "child_process (spawn/exec). Making a file executable has no purpose "
                "other than running it, so chmod+x followed by an exec/spawn is the "
                f"drop-and-run signature of a dropper/loader ({chain} payload"
                + (
                    "; a remote fetch is present, completing the download->chmod->"
                    "execute chain"
                    if has_fetch
                    else ""
                )
                + (
                    "; the chmod target and the exec target are the same symbol"
                    if shared
                    else ""
                )
                + "). The match requires the executable-bit operation and the "
                "execution sink together, so each individually benign part does not "
                "fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Confirm what file is being made executable and run, and where it "
                "came from. Fetching a remote file, chmod+x-ing it, and executing it "
                "is the dropper pattern; reject the extension and block the staging "
                "endpoint. A legitimate toolchain bootstrap should pin and verify "
                "the binary it downloads."
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
                snippet=snippet_at(text, match.start()) or "drop-and-run",
                line_number=line_number,
            )
        )


register(DownloadExecDropperRule())

__all__ = ["DownloadExecDropperRule"]
