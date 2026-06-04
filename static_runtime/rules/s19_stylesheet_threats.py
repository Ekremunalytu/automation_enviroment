"""S19 static rules: stylesheet-borne (CSS/LESS) attack TTPs.

Detection family for the `nextsecurity` / `trailofbits/vsix-zoo` stylesheet
corpus — a labelled dataset of CSS/LESS-borne TTPs packaged inside a malicious
VS Code extension. The corpus' premise is that a *stylesheet* can be a malware
carrier when the extension processes it: either compiled (LESS -> the extension
host's Node.js context) or rendered (CSS in a webview's Chromium renderer). This
module adds the three stylesheet-specific signals that the existing JS/manifest
rules (s1-s18) do not model. See
``documents/detection-design/nextsecurity-stylesheet-spec.md`` for the full
threat model, the TTP -> real-impact matrix, and the per-rule reasoning.

Three rules, deliberately scoped to **stylesheet files only** (``.css`` / ``.less``
/ ``.scss`` / ``.sass``). That scoping is what keeps them high-fidelity: a
backtick has no meaning in CSS except LESS inline-JavaScript, and a non-standard
URL scheme has no meaning in a webview stylesheet except a resource-load attempt.
Applying the same patterns to ``.js`` would false-positive catastrophically (every
template literal is a backtick) — so the rules consult ``_STYLESHEET_SUFFIXES``
and skip non-stylesheet documents.

* ``extrace.s19.stylesheet_inline_js`` — **CRITICAL / BLOCK.** A backtick-delimited
  span in a stylesheet is LESS inline JavaScript (``~`...` `` / `` `...` ``), which
  the LESS compiler ``eval``s at compile time **in the extension-host Node.js
  process** — full ``fs`` / ``child_process`` / ``net`` reach. This is the only
  true remote-code-execution vector in the corpus, so like ``s10``/``s11``/``s16``
  it convicts on the static signature alone (CRITICAL -> BLOCK, ADR 0016). less.js
  >= 3.0 defaults ``javascriptEnabled: false`` so the eval is conditional on the
  consuming build, but *shipping* inline JS in a stylesheet is unambiguous author
  intent with no benign explanation — exactly the win32-gated ``s11`` precedent
  (gated payload, still CRITICAL).
* ``extrace.s19.stylesheet_nonstandard_scheme`` — **MEDIUM / WARN.** A stylesheet
  resource loader (``@import`` / ``url()`` / ``src:``) targeting a non-standard
  scheme (``ftp:`` / ``ws:`` / ``wss:`` / ``gopher:`` / ``file:`` / ``javascript:``
  / ``vbscript:``). Most are inert in a modern Chromium webview (FTP removed, ws
  not importable), so the value is signature/author-intent + the live ``file:``
  local-read attempt — MEDIUM, never a blocker.
* ``extrace.s19.stylesheet_css_exfil`` — **MEDIUM / WARN.** The CSS-specific
  data-exfiltration shapes with no JS-rule analog: a substring/prefix/suffix
  attribute selector (the CSS-keylogger primitive, ``[value^=...]``) or a
  ``::before``/``::after`` ``content`` pseudo-element, whose declaration block
  fires a **remote** ``url()`` GET. URL/structural attribute selectors
  (``href``/``src``/``class``/``id``/...) are excluded because prefix-matching them
  with a remote icon is the legitimate external-link-icon pattern. MEDIUM/WARN:
  the egress is gated by the webview's CSP/``localResourceRoots`` (CSP-grading is a
  dynamic-plane refinement, spec §6), so this surfaces the shape for review.

All three stay ``adversary_class = None`` per the static-IOC convention
(architecture-reconciliation doc): in-house static rules report a capability/IOC
surface; adversary-class attribution belongs to the dynamic a-rules. The rule
logic is general (no ``nextsecurity`` literal); the corpus' synthetic IOCs live
only in the tests + the spec appendix.
"""

from __future__ import annotations

import re
from pathlib import Path

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

# Stylesheet sources only. The s19 patterns are high-fidelity *because* they are
# scoped here: a backtick / non-standard scheme is anomalous in a stylesheet but
# routine elsewhere (JS template literals, docs).
_STYLESHEET_SUFFIXES: frozenset[str] = frozenset({".css", ".less", ".scss", ".sass"})


def _iter_stylesheets(
    context: StaticAnalysisContext,
) -> list[tuple[str, str]]:
    """``(relative_path, text)`` for each stylesheet document (suffix-scoped)."""
    return [
        (relative_path, text)
        for relative_path, text in iter_text_documents(context)
        if Path(relative_path).suffix.lower() in _STYLESHEET_SUFFIXES
    ]


def _add_evidence(
    evidence: list[StaticEvidenceRef],
    context: StaticAnalysisContext,
    relative_path: str,
    text: str,
    match: re.Match[str] | None,
    fallback: str,
) -> None:
    if match is None or len(evidence) >= _MAX_EVIDENCE:
        return
    line_number = line_number_at(text, match.start())
    evidence.append(
        file_evidence(
            relative_path,
            evidence_type_for(context, relative_path),
            snippet=line_at(text, line_number) or fallback,
            line_number=line_number,
        )
    )


# ── S19a — LESS inline-JavaScript eval (RCE) ──────────────────────────────────
# A backtick-delimited span. CSS/SCSS/SASS have no backtick token, so any backtick
# pair in a stylesheet is LESS inline JavaScript: ``~`process...` `` (the ``~``
# escape is optional — the eval happens with or without it). Bounded to one line
# so a stray backtick in a multi-line comment cannot assemble an unbounded match.
_INLINE_JS_RE = re.compile(r"~?`[^`\n]*`")


class StylesheetInlineJsRule:
    rule_id = "extrace.s19.stylesheet_inline_js"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    # Class-less per the static-IOC convention; the conceptual class is dynamic
    # code execution (T1059). The dynamic twin would be a LESS-compile eval at
    # runtime — carried by the generic process/eval observables, not a new a-rule.
    adversary_class: AdversaryClass | None = None
    # CRITICAL -> BLOCK: inline JS in a stylesheet is compiled-time eval in the
    # extension-host Node context, a finished RCE primitive with no benign use.
    # Conditional on the build's javascriptEnabled (less.js >= 3.0 default-off),
    # exactly like s11's win32 gate — still CRITICAL on author intent.
    severity = Severity.CRITICAL
    description = (
        "Stylesheet contains LESS inline JavaScript (backtick eval), which the "
        "LESS compiler executes in the extension-host Node.js process — arbitrary "
        "code execution with full fs/child_process/net access."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in _iter_stylesheets(context):
            match = _INLINE_JS_RE.search(text)
            if match is None:
                continue
            return [self._finding(context, relative_path, text, match)]
        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        match: re.Match[str],
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        _add_evidence(
            evidence, context, relative_path, text, match, "less inline-js eval"
        )
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1059", "extrace.ext.stylesheet_inline_js"],
            severity=self.severity,
            confidence=Confidence.HIGH,
            title="Stylesheet carries LESS inline-JavaScript eval (RCE)",
            description=(
                "The extension ships a stylesheet containing LESS inline "
                "JavaScript: a backtick-delimited expression (`~`...`` or `` `...` "
                "``) that the LESS compiler evaluates with eval() at compile time. "
                "That code runs in the extension-host Node.js process — not the "
                "webview sandbox — so it has full fs, child_process, net and "
                "process.env access. A stylesheet has no legitimate reason to "
                "carry executable JavaScript; this is the one true remote-code-"
                "execution vector among the stylesheet TTPs. less.js 3.0+ defaults "
                "javascriptEnabled to false, so the eval is conditional on the "
                "consuming build, but shipping inline JS in a stylesheet is "
                "unambiguous malicious intent."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat inline JavaScript in a stylesheet as an RCE attempt — reject "
                "the extension. If the host compiles LESS, ensure javascriptEnabled "
                "is false (the less.js 3.0+ default) so the eval cannot fire."
            ),
        )


# ── S19b — non-standard-scheme stylesheet resource load ───────────────────────
# A resource loader (@import / url() / src:) wired to a non-standard scheme.
# ``[^;{}\n]{0,120}?`` keeps the loader and the scheme on one logical declaration
# and bounds the gap. The scheme is captured (group 1) for the evidence message.
_NONSTANDARD_SCHEME_RE = re.compile(
    r"(?:@import\b|\burl\s*\(|\bsrc\s*:)[^;{}\n]{0,120}?"
    r"\b(ftp|wss?|gopher|file|javascript|vbscript):",
    re.IGNORECASE,
)


class StylesheetNonstandardSchemeRule:
    rule_id = "extrace.s19.stylesheet_nonstandard_scheme"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # MEDIUM / WARN: most of these schemes are inert in a modern Chromium webview
    # (FTP removed, ws:// not importable via @import), so the value is signature /
    # author-intent plus the live file:// local-read attempt. Never a blocker.
    severity = Severity.MEDIUM
    description = (
        "Stylesheet resource loader (@import/url()/src:) targets a non-standard "
        "scheme (ftp/ws/wss/gopher/file/javascript/vbscript) — an anomalous "
        "fetch/local-read attempt with no legitimate use in a webview stylesheet."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in _iter_stylesheets(context):
            match = _NONSTANDARD_SCHEME_RE.search(text)
            if match is None:
                continue
            return [self._finding(context, relative_path, text, match)]
        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        match: re.Match[str],
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        _add_evidence(
            evidence, context, relative_path, text, match, "non-standard scheme load"
        )
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1071", "extrace.ext.stylesheet_nonstandard_scheme"],
            severity=self.severity,
            confidence=Confidence.MEDIUM,
            title="Stylesheet loads a resource over a non-standard scheme",
            description=(
                "The extension's stylesheet contains a resource loader "
                "(@import / url() / src:) that targets a non-standard URL scheme "
                "(ftp, ws/wss, gopher, file, javascript or vbscript). A modern "
                "Chromium webview ignores most of these (FTP support was removed; "
                "@import does not accept WebSocket schemes), so several are "
                "signature/intent-only — but a file:// reference is a local-file-"
                "read attempt (gated by the webview's localResourceRoots) and the "
                "whole pattern is anomalous in a stylesheet a benign extension "
                "would ship."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Stylesheets should only reference relative or https resources. "
                "Review why a non-standard scheme is present; a file:// reference "
                "is a local-read attempt and ftp/ws/gopher have no place in a "
                "webview stylesheet."
            ),
        )


# ── S19c — CSS-native data exfiltration (keylogger / content beacon) ───────────
# A remote url() sink — http(s) or protocol-relative (//host); a single leading
# slash (root-relative, local) does NOT match.
_REMOTE_URL = r"url\(\s*['\"]?(?:https?:)?//"

# Substring/prefix/suffix attribute selector (the CSS-keylogger primitive) whose
# block fires a remote url(). The negative lookahead drops URL/structural
# attributes (href/src/class/id/type/rel/role/aria/lang) where prefix-matching +
# a remote icon is the legitimate external-link-icon / BEM pattern; what remains
# is value-bearing attributes (value/password/data-*/title/alt/...) — the
# char-by-char input-exfil shape.
_ATTR_KEYLOGGER_RE = re.compile(
    r"\[\s*(?!(?:href|src|class|id|type|rel|role|aria|lang)\b)[\w-]+\s*[\^$*]="
    r"[^\]]*\][^{}]{0,200}\{[^}]{0,400}" + _REMOTE_URL,
    re.IGNORECASE | re.DOTALL,
)

# ::before / ::after content pseudo-element firing a remote url() — a GET on
# render that can carry a token in the URL. Legit pseudo-elements use text or
# local icons; a remote content url is the exfil/beacon shape.
_CONTENT_EXFIL_RE = re.compile(
    r"::?(?:before|after)\b[^{}]{0,200}\{[^}]{0,400}"
    r"content\s*:[^;}]*" + _REMOTE_URL,
    re.IGNORECASE | re.DOTALL,
)


class StylesheetCssExfilRule:
    rule_id = "extrace.s19.stylesheet_css_exfil"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # MEDIUM / WARN: the egress is gated by the webview CSP / localResourceRoots,
    # so static cannot prove exploitability — it surfaces the exfil shape for
    # review. CSP-grading is the dynamic-plane refinement (spec §6).
    severity = Severity.MEDIUM
    description = (
        "Stylesheet uses a CSS-native data-exfiltration shape — a substring "
        "attribute selector (CSS keylogger) or a ::before/::after content "
        "pseudo-element — to fire a remote url() GET that can leak input or beacon."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in _iter_stylesheets(context):
            keylogger = _ATTR_KEYLOGGER_RE.search(text)
            content = _CONTENT_EXFIL_RE.search(text)
            if keylogger is None and content is None:
                continue
            return [self._finding(context, relative_path, text, keylogger, content)]
        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        keylogger: re.Match[str] | None,
        content: re.Match[str] | None,
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        _add_evidence(
            evidence, context, relative_path, text, keylogger, "css attribute-exfil"
        )
        _add_evidence(
            evidence, context, relative_path, text, content, "css content-exfil"
        )
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=[
                "attack.T1041",
                "attack.T1056",
                "extrace.ext.stylesheet_css_exfil",
            ],
            severity=self.severity,
            confidence=Confidence.MEDIUM,
            title="Stylesheet uses a CSS-native exfiltration shape (keylogger/beacon)",
            description=(
                "The extension's stylesheet contains a CSS-native data-"
                "exfiltration construct that fires a remote url() request: either "
                "a substring/prefix/suffix attribute selector on a value-bearing "
                "attribute (the CSS-keylogger primitive — each matched input value "
                "triggers a unique GET, leaking the value to a remote endpoint), or "
                "a ::before/::after content pseudo-element that GETs a remote url "
                "(a render-time beacon that can carry a token in the URL). These "
                "are CSS-only data-plane techniques with no JavaScript-rule "
                "analogue. The remote-egress half is gated by the webview's CSP / "
                "localResourceRoots, so the shape is surfaced for review rather "
                "than convicted outright."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Stylesheets should not fire remote requests keyed off input "
                "values or render state. Pin the webview CSP (connect-src/img-src/"
                "font-src) and localResourceRoots; review the matched selector/"
                "pseudo-element for value exfiltration."
            ),
        )


register(StylesheetInlineJsRule())
register(StylesheetNonstandardSchemeRule())
register(StylesheetCssExfilRule())

__all__ = [
    "StylesheetCssExfilRule",
    "StylesheetInlineJsRule",
    "StylesheetNonstandardSchemeRule",
]
