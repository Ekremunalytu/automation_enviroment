from __future__ import annotations

import copy

from packages.analysis_contracts import ActivationReport
from packages.analysis_engine.rules.a3_typosquat import RULE
from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_a3_rule_fires_for_typosquat_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a3-typosquat-canary"
    )

    assert "extrace.a3.typosquat" in production_rule_ids(bundle)


def test_a3_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.a3.typosquat" not in production_rule_ids(bundle)


def test_a3_rule_is_silent_for_benign_theme_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-theme-0.0.1")

    assert "extrace.a3.typosquat" not in production_rule_ids(bundle)


def _report_with_identifier(identifier: str) -> ActivationReport:
    payload = {
        "report_version": 2,
        "target_extension_expected": identifier,
        "automation_health": {"status": "healthy", "reasons": []},
        "signal_summary": {},
        "summary": {"target_extension_version": "0.0.1"},
        "scenario_traces": [],
        "evidence_events": [
            {
                "event_id": "activation-0001",
                "kind": "extension_host",
                "rel_time_s": 0.0,
                "summary": f"Activated {identifier}",
                "raw_context": {"event_type": "activated"},
            }
        ],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
    }
    return ActivationReport.model_validate(copy.deepcopy(payload))


def test_a3_rule_ignores_exact_match_of_legit_popular_extension() -> None:
    """`ms-python.python` itself is the legit publisher — must stay silent."""

    findings = RULE.evaluate(_report_with_identifier("ms-python.python"))
    assert findings == []


def test_a3_rule_fires_on_distance_one_typo() -> None:
    """Dropping a character inside a popular id still triggers the rule."""

    findings = RULE.evaluate(_report_with_identifier("ms-pyton.python"))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.a3.typosquat"
    assert finding.severity.value == "high"
    assert finding.confidence.value == "medium"
    assert "ms-python.python" in finding.description
    assert finding.evidence, "finding must carry at least one evidence ref"


def test_a3_rule_is_silent_for_unrelated_identifier() -> None:
    """A genuinely different publisher.name must not fire."""

    findings = RULE.evaluate(
        _report_with_identifier("acme-corp.totally-unrelated-extension")
    )
    assert findings == []


def test_a3_rule_handles_empty_or_malformed_identifier() -> None:
    """No publisher.name split -> no finding, no exception."""

    assert RULE.evaluate(_report_with_identifier("")) == []
    assert RULE.evaluate(_report_with_identifier("no-dot-here")) == []
