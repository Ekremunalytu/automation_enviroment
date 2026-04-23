from __future__ import annotations

import json
from pathlib import Path

from packages.analysis_contracts.detection import RuleLifecycle
from packages.analysis_engine.rules.registry import get_production_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_ROOT = REPO_ROOT / "extensions" / "malicious"
EXPECTED_POC_CLASSES = {"A1", "A2", "A4", "A6"}
EXPECTED_PRODUCTION_RULE_IDS = {
    "extrace.a1.credential_read_then_network",
    "extrace.a2.startup_network_beacon",
    "extrace.a4.workspace_exfil",
    "extrace.a6.startup_ui_prompt",
}


def _manifests() -> list[dict[str, object]]:
    manifests: list[dict[str, object]] = []
    for label_path in sorted(MALICIOUS_ROOT.glob("*/LABEL.yaml")):
        manifests.append(json.loads(label_path.read_text(encoding="utf-8")))
    return manifests


def test_poc_canary_set_covers_the_expected_adversary_classes() -> None:
    manifests = _manifests()
    classes = {
        manifest["category"]["adversary_class"]
        for manifest in manifests
        if manifest["tier"] == "T1"
    }
    assert EXPECTED_POC_CLASSES.issubset(classes)


def test_every_t1_fixture_declares_at_least_one_detection_contract() -> None:
    manifests = _manifests()
    t1_manifests = [manifest for manifest in manifests if manifest["tier"] == "T1"]

    assert t1_manifests, "Week 5 requires at least one T1 canary manifest."
    for manifest in t1_manifests:
        must_fire = manifest["expected_detections"]["must_fire"]
        assert (
            must_fire
        ), f"{manifest['id']} must declare at least one rule expectation."


def test_live_fixtures_are_not_present_in_the_poc_scaffold() -> None:
    manifests = _manifests()
    assert all(manifest["tier"] != "T3" for manifest in manifests)


def test_get_production_rules_returns_all_four_poc_rules() -> None:
    """Registry must surface every PoC Must-class rule (A1/A2/A4/A6).

    Without this, dropping a rule from `_BUILTIN_RULE_MODULES` would only be
    caught by a downstream rule-specific test, which can be flaky to attribute.
    """

    production_rules = get_production_rules()
    rule_ids = {rule.rule_id for rule in production_rules}

    assert (
        rule_ids == EXPECTED_PRODUCTION_RULE_IDS
    ), f"production rule registry drifted: got {rule_ids}"


def test_every_production_rule_is_marked_production_lifecycle() -> None:
    """Production rules must declare `RuleLifecycle.PRODUCTION` so that the
    runner's malicious-without-production guard does not silently downgrade
    real findings to suspicious."""

    for rule in get_production_rules():
        assert (
            rule.lifecycle == RuleLifecycle.PRODUCTION
        ), f"{rule.rule_id} returned by get_production_rules but lifecycle={rule.lifecycle}"


def test_canary_must_fire_rule_ids_match_registered_rules() -> None:
    """T1 canary `must_fire` rule_ids must exist in the production registry.

    Catches the case where a canary references a renamed/removed rule_id.
    """

    registered = {rule.rule_id for rule in get_production_rules()}
    for manifest in _manifests():
        if manifest["tier"] != "T1":
            continue
        for expected_rule_id in manifest["expected_detections"]["must_fire"]:
            assert expected_rule_id in registered, (
                f"{manifest['id']} expects rule_id {expected_rule_id!r} "
                f"but registry has {sorted(registered)}"
            )
