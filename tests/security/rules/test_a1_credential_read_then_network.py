from __future__ import annotations

from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_a1_rule_fires_for_credential_read_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a1-credential-read-canary"
    )

    assert "extrace.a1.credential_read_then_network" in production_rule_ids(bundle)


def test_a1_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.a1.credential_read_then_network" not in production_rule_ids(bundle)
