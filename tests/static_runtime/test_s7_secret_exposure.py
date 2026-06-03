"""Fire / silent unit tests for the S7 hardcoded-secret rule.

The rule must flag the credential but NEVER quote it into evidence (the snippet
names the class only); both halves are asserted here.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s7_secret_exposure import HardcodedSecretRule

MakeContext = Callable[..., StaticAnalysisContext]

_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
_GH_TOKEN = "ghp_" + "b" * 36


def test_fires_on_aws_key_without_leaking_it(make_context: MakeContext) -> None:
    ctx = make_context(files={"a.js": f'const k = "{_AWS_KEY}";'})
    findings = HardcodedSecretRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s7.hardcoded_secret"
    assert finding.severity.value == "medium"
    assert "aws" in finding.description
    # The raw secret must never appear in evidence snippets.
    for ref in finding.evidence:
        assert _AWS_KEY not in (ref.snippet or "")
    assert finding.evidence[0].line_number == 1


def test_fires_on_github_token(make_context: MakeContext) -> None:
    ctx = make_context(files={"a.ts": f"const t = '{_GH_TOKEN}';"})
    findings = HardcodedSecretRule().evaluate(ctx)
    assert len(findings) == 1
    assert "github_token" in findings[0].description
    for ref in findings[0].evidence:
        assert _GH_TOKEN not in (ref.snippet or "")


def test_silent_for_clean_source(make_context: MakeContext) -> None:
    ctx = make_context(files={"a.js": "const apiBase = 'https://api.example.com';"})
    assert HardcodedSecretRule().evaluate(ctx) == []
