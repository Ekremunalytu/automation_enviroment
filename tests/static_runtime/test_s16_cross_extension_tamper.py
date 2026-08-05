"""Fire / silent / FP-guard unit tests for the S16 cross-extension-tamper rule.

Inputs are SYNTHETIC — hand-authored ~15-line reproductions of the *shape* of the
ecm3401 "Educational Attack Suite" Control-plane techniques (``func_tamper_docker``
overwriting another extension's bundle via ``getExtension().extensionPath``, and
``spoof_api`` rewriting a victim consumer through a ``.vscode/extensions`` path
literal). The real PoC is **never** downloaded into the repo; only the declawed
pattern is reproduced (see the detection-design README safety section). No live
payload, no real victim extension on disk.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s16_cross_extension_tamper import CrossExtensionTamperRule

MakeContext = Callable[..., StaticAnalysisContext]

# TAMPER1a (variable form): obtain another extension via getExtension, then copy
# an attacker bundle over its on-disk code — the func_tamper_docker shape.
_TAMPER_VIA_GETEXTENSION = """
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
function attack(context) {
  const target = vscode.extensions.getExtension("ms-azuretools.vscode-docker");
  const dst = path.join(target.extensionPath, "dist", "extension.bundle.js");
  const src = path.join(context.extensionPath, "resources", "attack.bundle.js");
  fs.copyFileSync(src, dst);
}
exports.attack = attack;
"""

# TAMPER1b (install-root literal): rewrite a victim consumer's installed file via
# a hand-built ~/.vscode/extensions/<victim> path — the spoof_api shape.
_TAMPER_VIA_INSTALL_ROOT = """
const fs = require("fs");
const os = require("os");
function repoint() {
  const victim = os.homedir() + "/.vscode/extensions/acme.consumer-0.0.1/out/extension.js";
  const patched = fs.readFileSync(victim, "utf8").replace("acme.honest", "acme.evil");
  fs.writeFileSync(victim, patched);
}
"""

# TAMPER1a (inline form): getExtension(...).extensionPath used directly in a sink.
_TAMPER_INLINE = """
const vscode = require("vscode");
const fs = require("fs");
fs.copyFileSync(myBundle, vscode.extensions.getExtension("other.ext").extensionPath + "/main.js");
"""


def test_fires_critical_on_getextension_tamper(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": _TAMPER_VIA_GETEXTENSION})
    findings = CrossExtensionTamperRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s16.cross_extension_tamper"
    assert finding.severity.value == "critical"
    assert finding.confidence.value == "high"
    assert finding.adversary_class is None
    assert "extrace.ext.cross_extension_tamper" in finding.categories
    assert "attack.T1554" in finding.categories
    assert finding.evidence


def test_fires_on_install_root_literal_write(make_context: MakeContext) -> None:
    ctx = make_context(files={"spoof.js": _TAMPER_VIA_INSTALL_ROOT})
    assert len(CrossExtensionTamperRule().evaluate(ctx)) == 1


def test_fires_on_inline_getextension_write(make_context: MakeContext) -> None:
    ctx = make_context(files={"ext.js": _TAMPER_INLINE})
    assert len(CrossExtensionTamperRule().evaluate(ctx)) == 1


def test_silent_for_write_to_own_extension_path(make_context: MakeContext) -> None:
    # The load-bearing FP guard: writing to the extension's OWN
    # context.extensionPath is allowlisted — not foreign-extension tampering.
    src = (
        'const fs = require("fs");\n'
        "function cache(context) {\n"
        '  const p = require("path").join(context.extensionPath, "cache.json");\n'
        "  fs.writeFileSync(p, JSON.stringify({}));\n"
        "}\n"
    )
    ctx = make_context(files={"extension.js": src})
    assert CrossExtensionTamperRule().evaluate(ctx) == []


def test_silent_for_write_to_global_storage(make_context: MakeContext) -> None:
    # Writing to the extension's own globalStorageUri is the normal persistence
    # path — must stay silent (no foreign extensionPath, no install-root literal).
    src = (
        'const fs = require("fs");\n'
        "function save(context) {\n"
        "  fs.writeFileSync(context.globalStorageUri.fsPath + '/state.json', '{}');\n"
        "}\n"
    )
    ctx = make_context(files={"extension.js": src})
    assert CrossExtensionTamperRule().evaluate(ctx) == []


def test_silent_for_reading_another_extension_without_write(
    make_context: MakeContext,
) -> None:
    # Capability check: read another extension's path / exports but never WRITE.
    # getExtension is ubiquitous; without a write into the foreign dir it is benign.
    src = (
        'const vscode = require("vscode");\n'
        'const fs = require("fs");\n'
        'const dep = vscode.extensions.getExtension("ms-python.python");\n'
        'const cfg = fs.readFileSync(dep.extensionPath + "/package.json", "utf8");\n'
    )
    ctx = make_context(files={"extension.js": src})
    assert CrossExtensionTamperRule().evaluate(ctx) == []


def test_silent_for_unproven_extension_uri_receiver(
    make_context: MakeContext,
) -> None:
    src = (
        "function cache(extension) {"
        "const dst = path.join(extension.extensionUri.fsPath, 'cache.json');"
        "fs.writeFileSync(dst, '{}');"
        "}"
    )
    ctx = make_context(files={"extension.js": src})
    assert CrossExtensionTamperRule().evaluate(ctx) == []


def test_silent_for_minified_variable_collision_across_bundle_regions(
    make_context: MakeContext,
) -> None:
    padding = "const bundledData = '" + ("x" * 9000) + "';"
    src = (
        'const target = vscode.extensions.getExtension("other.ext");'
        "const f = path.join(target.extensionPath, 'main.js');"
        + padding
        + "function unrelated(f) { fs.writeFileSync(f, '{}'); }"
    )
    ctx = make_context(files={"bundle.js": src})
    assert CrossExtensionTamperRule().evaluate(ctx) == []
