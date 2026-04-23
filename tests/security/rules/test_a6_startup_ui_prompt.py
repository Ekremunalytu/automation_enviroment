from __future__ import annotations

from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_a6_rule_fires_for_ui_spoof_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a6-ui-spoof-canary"
    )

    assert "extrace.a6.startup_ui_prompt" in production_rule_ids(bundle)


def test_a6_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.a6.startup_ui_prompt" not in production_rule_ids(bundle)
