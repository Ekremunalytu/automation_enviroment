"""S15 static rule: an extension's own local HTTP/webview surface is an
unguarded arbitrary-local-file-read primitive (the VLN5 conjunction).

This is the first rule on a **new, orthogonal axis**: it does not ask "is this
extension *malicious*?" (the S/RS/DR/UC/NL malice axis) but "does this *legitimate*
extension ship an *exploitable insecure pattern*?". The design driver is the
2021 Snyk-labs Instant Markdown class (and its recurring descendants — Live
Server ``CVE-2025-65717``, Markdown Preview Enhanced ``CVE-2025-65716``), where a
benign markdown-preview extension stands up a local static HTTP server that maps
a request path straight onto the filesystem with **no path-traversal guard**, and
exposes that server to the browser via permissive CORS (or renders untrusted
content in a CSP-less webview). A malicious web page the developer opens can then
reach ``localhost`` and read ``../../../../home/<user>/.ssh/id_rsa`` off disk. The
*content* and *exfil infrastructure* of that chain live in the attacker's web
page and receiver — out of ExTrace's scope; the *vulnerable primitive* lives in
the extension source, which is exactly what this rule sees. See
``documents/detection-design/snyk-labs-vln-detection-spec.md``.

Like ``s11``/``s13`` the rule keys on the **conjunction, never the parts** — and
here the conjunction is unusually load-bearing because every part alone is wildly
benign. Dozens of legitimate extensions (Live Preview, dev-server, LSP-over-http)
stand up a local HTTP server (VLN1); plenty read files in response to requests
(VLN2); permissive CORS (VLN4) and webviews (VLN3) are everywhere. The signal is
**not** any of those — it is the single file where all of:

  (VLN1) a local HTTP server (``http.createServer`` / ``express()`` / ``.listen``),
  (VLN2) a request-derived path flowing into a filesystem read sink
         (``req.url``/``req.params`` -> ``fs.readFile`` / ``res.sendFile``),
  with **no containment guard** (no ``path.resolve(...)`` + ``startsWith(root)``
         check, and no hardened static lib such as ``send`` / ``serve-static``
         that does containment for you), and
  (reachable origin) either permissive CORS (VLN4, ``Access-Control-Allow-Origin:
         "*"``) **or** a CSP-less webview render (VLN3),

co-occur. That conjunction is a finished arbitrary-local-file-read primitive: the
exploit's content half is not even needed to convict the *vulnerability*, because
the primitive is in the extension itself.

**FP discipline is the whole game.** Flagging a *guarded* local server destroys
user trust (the extension is benign and correct). So the guard detection is
deliberately **conservative** — if a ``path.resolve``/``normalize`` co-occurs with
a ``startsWith`` containment check, or a hardened static lib is imported, the rule
goes **silent** even at some cost of a false negative. The honest static limit:
this approximates the spec's taint (request-path -> fs sink, guard = sanitizer) by
file-level co-occurrence rather than true dataflow, so a hardened-lib-with-a-logic-
bug or a config/runtime-gated server path is a documented miss (spec §7).

This is a **VULNERABILITY surface, not a malice conviction**, so unlike ``s10``/
``s11`` it is **MEDIUM / WARN, never CRITICAL / BLOCK**: a vulnerable-but-benign
extension must surface for review, not be rejected before the sandbox. It stays
``adversary_class=None`` (the static-IOC convention; and adversary attribution is
the *wrong axis* for a vulnerability anyway). The orthogonal ``VULNERABLE`` verdict
axis the spec proposes (§6) is a shared-contract change held for owner sign-off;
until then this finding rides the existing malice-severity field at MEDIUM/WARN,
which the spec's reconciliation documents as a deliberate stopgap.
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

# VLN1 — a local HTTP server is stood up. ``.listen(<num/var>)`` covers the
# express/connect ``app.listen(8090)`` shape without matching DOM event
# listeners (``addEventListener``/``.on(...)`` are a different surface).
_SERVER_RE = re.compile(
    r"http\.createServer\s*\("
    r"|require\(\s*['\"](?:node:)?http['\"]\s*\)\s*\.createServer"
    r"|\bexpress\s*\(\s*\)"
    r"|\bconnect\s*\(\s*\)"
    r"|\.listen\s*\(\s*[\w'\"]",
)

# VLN2 source — a request-derived path. ``req``/``request`` ``.url``/``.path``/
# ``.params``/``.query`` or a URL parsed from one.
_REQ_PATH_RE = re.compile(
    r"\breq(?:uest)?\s*\.\s*(?:url|path|params|query)\b"
    r"|new\s+URL\s*\([^)]*\breq(?:uest)?\b",
)

# VLN2 sink — a filesystem read keyed off that path.
_FS_READ_SINK_RE = re.compile(
    r"\bfs\s*\.\s*(?:readFile|readFileSync|createReadStream)\s*\("
    r"|\.\s*sendFile\s*\(",
)

# The containment guard (sanitizer). Either a hardened static lib (which does
# root-containment internally), or a ``path.resolve``/``path.normalize`` paired
# with a ``startsWith`` root check within a bounded window (either order). This
# is intentionally broad: any plausible containment makes the rule go silent —
# we accept the false negative to never flag a correctly-guarded server.
_GUARD_RE = re.compile(
    r"require\(\s*['\"](?:serve-static|send)['\"]\s*\)"
    r"|\bserveStatic\s*\("
    r"|path\s*\.\s*(?:resolve|normalize)\b[\s\S]{0,400}?\.\s*startsWith\s*\("
    r"|\.\s*startsWith\s*\([\s\S]{0,400}?path\s*\.\s*(?:resolve|normalize)\b",
)

# VLN4 — permissive CORS: the local server is reachable cross-origin, so a
# browser page can drive the path traversal. ``Access-Control-Allow-Origin``
# header set to ``*`` (with quoting/spacing slack between header and value).
_PERMISSIVE_CORS_RE = re.compile(
    r"Access-Control-Allow-Origin['\"]?[^\n]{0,40}\*",
    re.IGNORECASE,
)

# VLN3 — the webview reachable-origin variant: untrusted content rendered into a
# webview with scripts enabled and no CSP. Presence detected here; CSP-absence is
# checked separately so a file that sets a CSP meta tag does not fire.
_WEBVIEW_RE = re.compile(
    r"\bwebview\s*\.\s*html\s*=|\benableScripts\s*:\s*true\b",
)
_CSP_RE = re.compile(r"content-security-policy", re.IGNORECASE)


class PathTraversalServerRule:
    rule_id = "extrace.s15.path_traversal_server"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    # Class-less: in-house static rules report a capability/IOC surface and leave
    # adversary attribution to the dynamic a-rules — and adversary class is the
    # wrong axis for a vulnerability-in-a-legit-extension anyway (spec §6).
    adversary_class: AdversaryClass | None = None
    # MEDIUM / WARN, NOT CRITICAL / BLOCK: this is a VULNERABILITY surface in a
    # (potentially benign) extension, not a malice conviction. Rejecting a
    # vulnerable-but-benign extension before the sandbox would be a trust-
    # destroying false positive; the finding surfaces for review/escalation.
    severity = Severity.MEDIUM
    description = (
        "Extension stands up a local HTTP/webview surface that maps a "
        "request-derived path onto a filesystem read with no containment guard "
        "and is reachable cross-origin — an arbitrary-local-file-read primitive "
        "(path traversal)."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            if not _SERVER_RE.search(text):
                continue
            if not (_REQ_PATH_RE.search(text) and _FS_READ_SINK_RE.search(text)):
                continue
            if _GUARD_RE.search(text):
                # Correctly guarded (resolve+containment, or a hardened static
                # lib) — the primitive is closed; stay silent.
                continue
            reachable = self._reachable_origin(text)
            if reachable is None:
                continue
            return [self._finding(context, relative_path, text, reachable)]
        return []

    @staticmethod
    def _reachable_origin(text: str) -> re.Pattern[str] | None:
        """Return the pattern proving the server is reachable, or None.

        Permissive CORS (VLN4) directly exposes the HTTP server cross-origin; a
        CSP-less scripted webview (VLN3) is the render-side variant of the same
        reachable-origin condition. A webview that ships a CSP meta tag is
        treated as defended and does not count.
        """
        if _PERMISSIVE_CORS_RE.search(text):
            return _PERMISSIVE_CORS_RE
        if _WEBVIEW_RE.search(text) and not _CSP_RE.search(text):
            return _WEBVIEW_RE
        return None

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        reachable: re.Pattern[str],
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        # The two load-bearing conjuncts (request-path sink and the missing-guard
        # server) first, then the reachable-origin proof.
        for pattern in (_FS_READ_SINK_RE, _SERVER_RE, reachable):
            self._add_first_match(evidence, context, relative_path, text, pattern)

        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=[
                "attack.T1083",
                "attack.T1005",
                "extrace.ext.path_traversal_server",
            ],
            severity=self.severity,
            confidence=Confidence.MEDIUM,
            title=("Local server is an unguarded arbitrary-file-read primitive"),
            description=(
                "The extension source stands up a local HTTP/webview surface that "
                "feeds a request-derived path into a filesystem read "
                "(fs.readFile / res.sendFile) with no path-traversal containment "
                "guard (no path.resolve + startsWith(root) check and no hardened "
                "static library), and exposes that surface cross-origin via "
                "permissive CORS or a CSP-less scripted webview. Together these "
                "form an arbitrary-local-file-read primitive: a malicious web page "
                "the developer opens can reach the local server and read files "
                "outside the intended root (e.g. SSH keys, credentials). This is a "
                "VULNERABILITY in a possibly-benign extension, not evidence of "
                "malice; the match requires the server, the unguarded request->read "
                "flow, and the reachable origin together, so each individually "
                "benign part does not fire."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Serve files through a hardened static library (send / "
                "serve-static) or add an explicit containment check "
                "(path.resolve(root, reqPath) and verify the result "
                "startsWith(root)); restrict the server's CORS origin to a known "
                "value and set a Content-Security-Policy on any webview. Treat as "
                "a path-traversal / arbitrary-file-read vulnerability for review."
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
                snippet=line_at(text, line_number) or "path-traversal server",
                line_number=line_number,
            )
        )


register(PathTraversalServerRule())

__all__ = ["PathTraversalServerRule"]
