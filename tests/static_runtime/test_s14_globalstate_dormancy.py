"""Fire / silent unit tests for the S14 globalState dormancy rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s14_globalstate_dormancy import GlobalStateDormancyRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_on_globalstate_timestamp_throttle(
    make_context: MakeContext,
) -> None:
    source = """
function activate(context) {
  const lastActivated = context.globalState.get("activationState", 0);
  const currentTime = Date.now();
  if (currentTime - lastActivated > 2 * 24 * 60 * 60 * 1000) {
    init();
    context.globalState.update("activationState", currentTime);
  }
}
"""
    ctx = make_context(files={"extension.js": source})
    findings = GlobalStateDormancyRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s14.globalstate_dormancy"
    assert finding.severity.value == "medium"
    assert "fresh VS Code profile/globalState" in (finding.mitigation_hint or "")


def test_silent_for_plain_globalstate_setting(make_context: MakeContext) -> None:
    source = """
function activate(context) {
  context.globalState.update("themeSeen", true);
}
"""
    ctx = make_context(files={"extension.js": source})
    assert GlobalStateDormancyRule().evaluate(ctx) == []


def test_silent_for_unrelated_bundle_regions(make_context: MakeContext) -> None:
    padding = "const bundledData = '" + ("x" * 9000) + "';"
    src = (
        'context.globalState.get("theme"); context.globalState.update("theme", value);'
        + padding
        + "if (Date.now() > lastRun + 86400000) activate();"
    )
    ctx = make_context(files={"bundle.js": src})
    assert GlobalStateDormancyRule().evaluate(ctx) == []
