from __future__ import annotations

from packages.analysis_contracts.detection import Verdict
from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_demo_rule_fires_for_runnable_demo_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-demo-runnable-canary"
    )

    assert "extrace.demo.runnable_canary" in production_rule_ids(bundle)
    assert bundle.detection_report.verdict == Verdict.MALICIOUS


def test_demo_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.demo.runnable_canary" not in production_rule_ids(bundle)
