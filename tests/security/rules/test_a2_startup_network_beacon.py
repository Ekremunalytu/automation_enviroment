from __future__ import annotations

from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_a2_rule_fires_for_startup_network_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a2-startup-network-canary"
    )

    assert "extrace.a2.startup_network_beacon" in production_rule_ids(bundle)


def test_a2_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.a2.startup_network_beacon" not in production_rule_ids(bundle)
