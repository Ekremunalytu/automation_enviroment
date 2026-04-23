from __future__ import annotations

from tests.security.helpers import REPO_ROOT, analyze_fixture, production_rule_ids


def test_a4_rule_fires_for_workspace_exfil_canary() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "malicious" / "t1-a4-workspace-exfil-canary"
    )

    assert "extrace.a4.workspace_exfil" in production_rule_ids(bundle)


def test_a4_rule_is_silent_for_benign_chat_fixture() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert "extrace.a4.workspace_exfil" not in production_rule_ids(bundle)
