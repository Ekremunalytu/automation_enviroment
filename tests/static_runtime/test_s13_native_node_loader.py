"""Fire / silent unit tests for the S13 native .node loader rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s13_native_node_loader import NativeNodeLoaderRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_critical_for_glassworm_style_theme_native_loader(
    make_context: MakeContext,
) -> None:
    source = """
const os = require("os");
function activate(context) {
  const platform = os.platform();
  let native;
  if (platform === "win32") {
    native = require("./dist/extension/desktop/os.node");
  } else if (platform === "darwin") {
    native = require("./dist/extension/desktop/darwin.node");
  }
  if (native) {
    native.init(platform, process.execPath, __dirname);
  }
}
"""
    ctx = make_context(
        manifest={
            "publisher": "bad",
            "name": "icon-theme-materiall",
            "displayName": "Material Icon Theme",
            "categories": ["Themes"],
            "contributes": {"iconThemes": [{"id": "material"}]},
        },
        files={"extension.js": source},
    )

    findings = NativeNodeLoaderRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s13.native_node_loader"
    assert finding.severity.value == "critical"
    assert "platform dispatch" in finding.description
    assert "process.execPath" in finding.description
    assert "no linux branch" in finding.description
    assert "extrace.host.platform_gate" in finding.categories


def test_plain_native_addon_load_warns_but_does_not_block(
    make_context: MakeContext,
) -> None:
    ctx = make_context(
        manifest={"publisher": "acme", "name": "native-parser"},
        files={"extension.js": 'const parser = require("./build/parser.node");'},
    )
    findings = NativeNodeLoaderRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].severity.value == "medium"


def test_silent_when_source_only_mentions_node_in_documentation(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"README.md": "This extension is not a .node addon."})
    assert NativeNodeLoaderRule().evaluate(ctx) == []
