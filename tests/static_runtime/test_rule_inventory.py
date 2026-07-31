"""SMF-0 live rule inventory and deterministic bundle fingerprint tests."""

from __future__ import annotations

import re

from static_runtime.rule_inventory import build_rule_bundle_inventory

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_rule_bundle_inventory_matches_live_production_counts() -> None:
    inventory = build_rule_bundle_inventory()

    assert len(inventory.inhouse_rules) == 26
    assert len(inventory.semgrep_rules) == 16
    assert [entry.rule_id for entry in inventory.inhouse_rules] == sorted(
        entry.rule_id for entry in inventory.inhouse_rules
    )
    assert [entry.rule_id for entry in inventory.semgrep_rules] == sorted(
        entry.rule_id for entry in inventory.semgrep_rules
    )
    assert all(
        entry.rule_lifecycle == "production" for entry in inventory.inhouse_rules
    )
    assert all(
        entry.rule_lifecycle == "production" for entry in inventory.semgrep_rules
    )
    assert all(
        entry.capabilities
        and entry.artifact_roles
        and entry.positive_tests
        and entry.negative_tests
        and entry.runtime_budget
        for entry in (*inventory.inhouse_rules, *inventory.semgrep_rules)
    )


def test_rule_bundle_fingerprint_is_stable_and_path_independent() -> None:
    first = build_rule_bundle_inventory()
    second = build_rule_bundle_inventory()

    assert first == second
    assert _SHA256_RE.fullmatch(first.rules_bundle_fingerprint)
    assert first.semgrep_rule_sources
    assert all(not path.startswith("/") for path, _ in first.semgrep_rule_sources)
    assert all(_SHA256_RE.fullmatch(digest) for _, digest in first.semgrep_rule_sources)


def test_rule_bundle_fingerprint_covers_rule_metadata_and_exact_yaml_bytes(
    monkeypatch,
) -> None:
    from static_runtime import rule_inventory

    baseline = build_rule_bundle_inventory().rules_bundle_fingerprint
    monkeypatch.setattr(
        rule_inventory,
        "get_semgrep_rule_source_digests",
        lambda: (("extrace-vsix-js.yml", "0" * 64),),
    )

    changed = build_rule_bundle_inventory().rules_bundle_fingerprint

    assert changed != baseline
