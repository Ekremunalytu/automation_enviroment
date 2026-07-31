"""S16 static rule: an extension writes into *another* extension's install
directory — foreign-extension tampering (the ecm3401 TAMPER1 invariant).

This is the **crown-jewel** rule of the ecm3401 "Educational Attack Suite"
(University of Exeter ECM3401 dissertation PoC) class. Two of that suite's
techniques — ``func_tamper_docker`` (overwrite ``ms-azuretools.vscode-docker``'s
``dist/extension.bundle.js`` with an attacker bundle via ``fs.copyFileSync``) and
``spoof_api`` (rewrite a victim consumer extension's ``out/extension.js`` /
``package.json`` so it loads a malicious API provider) — both reduce to a single
observable, near-zero-FP static primitive: **a write/copy sink whose destination
is a *foreign* extension's on-disk code.** See
``documents/detection-design/ecm3401-malicious-suite-spec.md`` (signal TAMPER1).

Why this is high-fidelity. VS Code carries an implicit trust assumption that *an
installed extension's on-disk code is immutable after install*. It is not: there
is no integrity check on ``~/.vscode/extensions/`` and it is a world-writable
user directory. An extension that copies its own bundle over another extension's
bundle achieves **persistence + execution hijack** entirely on the local disk,
never touching the marketplace — the foreign extension simply runs attacker code
the next time it activates. Almost no legitimate extension ever writes into a
*different* extension's directory (the rare exception — an "extension pack" /
installer — is documented below), so keying on that write is structurally rare.

The rule keys on the **conjunction (write sink + foreign target), never the
parts**. A write sink alone is benign (every extension writes to its own
``globalStorage`` / ``workspaceState``); a reference to another extension is
benign (capability checks via ``getExtension`` are ubiquitous). It is the write
*into a foreign extension's path* that has no benign explanation. Three sub-shapes
all collapse to that primitive, matched here:

  * **TAMPER1a (variable form)** — ``const ext = getExtension(id); ...
    fs.copyFileSync(src, path.join(ext.extensionPath, ...))``: a write/copy sink
    whose argument references a ``.extensionPath`` / ``.extensionUri`` on a
    receiver proven by a nearby ``getExtension`` assignment. An arbitrary
    receiver name is not treated as foreign.
  * **TAMPER1a (inline form)** — ``getExtension(id).extensionPath`` used directly
    inside a write/copy sink.
  * **TAMPER1b (install-root literal)** — a write/copy sink whose path argument
    contains a ``.vscode/extensions/`` (or ``.vscode-server`` / ``.vscode-oss`` /
    ``.cursor`` / ``vscodium`` / ``windsurf``) install-root literal. This catches
    the ``spoof_api`` consumer-rewrite, which builds the path by string concat
    (``os.homedir() + "/.vscode/extensions/<victim>/out/extension.js"``) and never
    calls ``getExtension``.

Like ``s10`` / ``s11`` / ``s12`` / ``s13`` this is **CRITICAL** and BLOCKs at the
static gate before the sandbox runs (ADR 0016: CRITICAL -> BLOCK /
``rejected_static``): a foreign-extension overwrite is not a capability surface to
review but a finished persistence / execution-hijack primitive. ``adversary_class``
stays ``None`` per the static-IOC convention (the reconciliation doc: in-house
static rules report a capability/IOC surface; adversary-class attribution belongs
to the dynamic plane). The rule logic is general-purpose — no ecm3401 literal; the
sample IOCs live only in tests + the spec appendix.

**Honest FP boundary.** The one known legitimate pattern that touches
``~/.vscode/extensions/`` is an *extension-pack / installer* extension. That is
rare and arguably *should* be reviewed; the spec documents it as the single
negative-fixture case. Writing to the extension's **own** directory
(``context.extensionPath`` / ``context.globalStorageUri`` / ``storageUri``) is
never fires without foreign provenance. The static limit (spec §7): a tamper that
builds the destination path entirely from runtime-derived variables with no
``.extensionPath`` token and no install-root literal in the sink call is a
documented miss, left to the dynamic plane (an ``openat``/``write`` into a foreign
extension dir is observable at runtime).
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
_MAX_DATAFLOW_SPAN = 8 * 1024

# A filesystem *write / copy* sink. ``fs.``-qualified or the unambiguous bare
# forms (the *Sync names and the create/copy/write/append family). Read-only
# primitives are deliberately excluded — reading another extension's files is a
# weaker signal; the conviction is a *write* into a foreign extension's tree. The
# alternation prefix is shared by all the TAMPER1 sub-patterns below.
_WRITE_SINK = (
    r"(?:fs\s*\.\s*)?"
    r"(?:copyFileSync|copyFile|writeFileSync|writeFile|createWriteStream|"
    r"appendFileSync|appendFile|cpSync)\s*\("
)
_WRITE_SINK_CALL_RE = re.compile(_WRITE_SINK)

# A filesystem read primitive — used only to *reject* a path-variable assignment
# whose RHS is a read (``const cfg = fs.readFileSync(other.extensionPath, ...)``
# binds file *contents*, not a path, so the var is not a foreign write target).
_FS_READ_RE = re.compile(
    r"\b(?:fs\s*\.\s*)?(?:readFileSync|readFile|createReadStream)\s*\("
)

# TAMPER1a (variable form) — a write/copy sink whose arguments reference a
# ``.extensionPath`` / ``.extensionUri`` on a receiver. The receiver identifier
# is captured (group 1) and must be proven by a nearby ``getExtension``
# assignment. ``[^;{}]{0,300}?`` keeps the match inside one call's argument list.
# The bounded window between a sink's open-paren and a token inside its argument
# list (one call; no statement break).
_SINK_GAP = r"[^;{}]{0,300}?"
_EXT_PATH_SUFFIX = r"\.\s*(?:extensionPath|extensionUri)\b"
_EXT_PATH_IN_SINK_RE = re.compile(
    _WRITE_SINK + _SINK_GAP + r"([A-Za-z_$][\w$]*)\s*" + _EXT_PATH_SUFFIX
)

# TAMPER1a (inline form) — ``getExtension(id).extensionPath`` (or ``.extensionUri``)
# used directly inside a write/copy sink call. You do not normally ``getExtension``
# your own id inline and write to it, so this is inherently a foreign target.
_INLINE_FOREIGN_WRITE_RE = re.compile(
    _WRITE_SINK + _SINK_GAP + r"getExtension\s*\([^)]*\)\s*[!?]*\s*" + _EXT_PATH_SUFFIX
)

# An extensions install-root path literal (``~/.vscode/extensions/`` and the
# common forks/servers). Own files are reached via ``context.extensionPath``,
# never a hand-built install-root literal, so this denotes the install root of
# *some* extension.
_INSTALL_ROOT_LITERAL = (
    r"\.(?:vscode(?:-server|-oss|-insiders)?|vscodium|cursor|windsurf)"
    r"[\\/]+extensions[\\/]"
)
_INSTALL_ROOT_LITERAL_RE = re.compile(_INSTALL_ROOT_LITERAL)

# TAMPER1b (inline form) — a write/copy sink whose path argument *directly*
# contains the install-root literal.
_INSTALL_ROOT_WRITE_RE = re.compile(_WRITE_SINK + _SINK_GAP + _INSTALL_ROOT_LITERAL)

# Variable-form support — the destination is built into a variable first
# (``const victim = os.homedir() + "/.vscode/extensions/<v>/out/extension.js"``;
# ``const dst = path.join(target.extensionPath, ...)``), then passed to the sink,
# so the foreign token is not inside the sink call. Capture every assignment's LHS
# (group 1) and RHS (group 2); a foreign-target var is one whose RHS names a
# foreign extension path. A RHS that is itself a read primitive binds *contents*,
# not a path, and is excluded.
_ASSIGN_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*=\s*([^;\n]*)")
# The receiver identifier (group 1) of an ``.extensionPath`` / ``.extensionUri``
# reference, so the own-context allowlist can be applied to an RHS.
_EXT_PATH_RECEIVER_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*\.\s*(?:extensionPath|extensionUri)\b"
)
_GET_EXTENSION_ASSIGN_RE = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
    r"[^;{}\n]{0,300}?\bgetExtension\s*\("
)
_INLINE_GET_EXTENSION_PATH_RE = re.compile(
    r"\bgetExtension\s*\([^)]*\)\s*[!?]*\s*" + _EXT_PATH_SUFFIX
)


class CrossExtensionTamperRule:
    rule_id = "extrace.s16.cross_extension_tamper"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    # Class-less per the static-IOC convention (reconciliation doc): in-house
    # static rules report a capability/IOC surface and leave adversary-class
    # attribution to the dynamic a-rules.
    adversary_class: AdversaryClass | None = None
    # CRITICAL -> BLOCK before the sandbox: overwriting another extension's
    # on-disk code is a finished persistence / execution-hijack primitive with no
    # benign explanation for a normal extension.
    severity = Severity.CRITICAL
    description = (
        "Extension writes/copies a file into another extension's install "
        "directory (foreign extensionPath or a .vscode/extensions install-root "
        "path), the persistence / execution-hijack primitive of a cross-extension "
        "tamper."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            match = self._foreign_write_match(text)
            if match is None:
                continue
            return [self._finding(context, relative_path, text, match)]
        return []

    @staticmethod
    def _foreign_write_match(text: str) -> re.Match[str] | None:
        """Return the match proving a write into a *foreign* extension, or None.

        In order: the install-root literal (TAMPER1b) and the inline-getExtension
        sink — both inherently foreign — then a foreign ``.extensionPath`` directly
        inside a sink call, then the variable form (a sink whose argument is a
        variable that holds a foreign ``.extensionPath``). The own-context
        allowlist is applied throughout so a write to the extension's own
        ``context.extensionPath`` never fires.
        """
        install_root = _INSTALL_ROOT_WRITE_RE.search(text)
        if install_root is not None:
            return install_root
        inline = _INLINE_FOREIGN_WRITE_RE.search(text)
        if inline is not None:
            return inline
        foreign_receivers = [
            (match.group(1), match.start())
            for match in _GET_EXTENSION_ASSIGN_RE.finditer(text)
        ]
        if (
            not foreign_receivers
            and _INSTALL_ROOT_LITERAL_RE.search(text) is None
            and _INLINE_GET_EXTENSION_PATH_RE.search(text) is None
        ):
            # Without a proven foreign receiver or install-root path, the
            # assignment/dataflow pass cannot produce a finding. Avoid parsing
            # every assignment in large minified bundles only to rediscover
            # that prerequisite is absent.
            return None
        for candidate in _EXT_PATH_IN_SINK_RE.finditer(text):
            if any(
                receiver == candidate.group(1)
                and 0 <= candidate.start() - assigned_at <= _MAX_DATAFLOW_SPAN
                for receiver, assigned_at in foreign_receivers
            ):
                return candidate
        return CrossExtensionTamperRule._variable_form_match(
            text, foreign_receivers=foreign_receivers
        )

    @staticmethod
    def _variable_form_match(
        text: str,
        *,
        foreign_receivers: list[tuple[str, int]],
    ) -> re.Match[str] | None:
        """A write sink whose argument is a variable holding a foreign path."""
        foreign_vars = [
            (assign.group(1), assign.start())
            for assign in _ASSIGN_RE.finditer(text)
            if any(
                token in assign.group(2)
                for token in (
                    "extensionPath",
                    "extensionUri",
                    "getExtension",
                    "extensions",
                )
            )
            if CrossExtensionTamperRule._rhs_is_foreign_path(
                assign.group(2),
                assignment_start=assign.start(),
                foreign_receivers=foreign_receivers,
            )
        ]
        if not foreign_vars:
            return None
        for sink in _WRITE_SINK_CALL_RE.finditer(text):
            args = text[sink.end() : sink.end() + 300]
            if any(
                0 <= sink.start() - assigned_at <= _MAX_DATAFLOW_SPAN
                and re.search(rf"\b{re.escape(var)}\b", args)
                for var, assigned_at in foreign_vars
            ):
                return sink
        return None

    @staticmethod
    def _rhs_is_foreign_path(
        rhs: str,
        *,
        assignment_start: int,
        foreign_receivers: list[tuple[str, int]],
    ) -> bool:
        """True if an assignment RHS builds a *foreign* extension path.

        Either an install-root literal, or a non-own ``.extensionPath`` receiver.
        A RHS that reads a file binds contents (not a path) and is excluded.
        """
        if _FS_READ_RE.search(rhs) is not None:
            return False
        if _INSTALL_ROOT_LITERAL_RE.search(rhs) is not None:
            return True
        if _INLINE_GET_EXTENSION_PATH_RE.search(rhs) is not None:
            return True
        rhs_receivers = {
            receiver.group(1) for receiver in _EXT_PATH_RECEIVER_RE.finditer(rhs)
        }
        return any(
            receiver in rhs_receivers
            and 0 <= assignment_start - assigned_at <= _MAX_DATAFLOW_SPAN
            for receiver, assigned_at in foreign_receivers
        )

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        match: re.Match[str],
    ) -> StaticDetectionFinding:
        line_number = line_number_at(text, match.start())
        evidence: list[StaticEvidenceRef] = [
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=snippet_at(text, match.start()) or "cross-extension write",
                line_number=line_number,
            )
        ]
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=[
                "attack.T1554",
                "attack.T1574",
                "extrace.ext.cross_extension_tamper",
            ],
            severity=self.severity,
            confidence=Confidence.HIGH,
            title="Extension overwrites another extension's installed files",
            description=(
                "The extension source writes or copies a file into another "
                "extension's install directory — either a write/copy sink targeting "
                "a foreign extension's extensionPath/extensionUri (obtained via "
                "getExtension), or a write into a .vscode/extensions install-root "
                "path. VS Code performs no integrity check on installed extensions, "
                "so overwriting another extension's on-disk code makes that "
                "extension run attacker code on its next activation — local "
                "persistence and execution hijack with no marketplace involvement. "
                "The match requires the write sink AND a foreign-extension target "
                "together; writing to the extension's own context.extensionPath / "
                "globalStorage is allowlisted and does not fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat a write into another extension's install directory as a "
                "tamper / persistence attempt — there is no legitimate reason for "
                "an extension to modify another extension's files. Reject the "
                "extension and verify the integrity of the targeted extension."
            ),
        )


register(CrossExtensionTamperRule())

__all__ = ["CrossExtensionTamperRule"]
