"""Deterministic live rule identity and bundle fingerprint for SMF-0.

This module intentionally exposes only metadata that can be derived from the
production in-house registry and Semgrep mapper. Human-reviewed capability,
test-ownership, false-positive, and blind-spot fields belong to the later
machine-readable SMF-0 inventory artifact; they are not guessed here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from static_runtime.rules.registry import get_production_rules
from static_runtime.semgrep_runner import (
    SemgrepRuleInventoryEntry,
    get_semgrep_rule_inventory,
    get_semgrep_rule_source_digests,
    get_semgrep_version,
)

RULE_BUNDLE_FINGERPRINT_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class InhouseRuleInventoryEntry:
    """Code-derived identity fields for one production in-house rule."""

    rule_id: str
    rule_version: str
    rule_lifecycle: str
    severity: str
    adversary_class: str | None


@dataclass(frozen=True, slots=True)
class StaticRuleBundleInventory:
    """Stable inventory of the rule inputs that determine the bundle fingerprint."""

    schema_version: str
    inhouse_rules: tuple[InhouseRuleInventoryEntry, ...]
    semgrep_rules: tuple[SemgrepRuleInventoryEntry, ...]
    semgrep_version: str
    semgrep_rule_sources: tuple[tuple[str, str], ...]
    rules_bundle_fingerprint: str


def build_rule_bundle_inventory() -> StaticRuleBundleInventory:
    """Build the live, deterministically ordered SMF-0 rule-bundle inventory."""

    inhouse_rules = tuple(
        InhouseRuleInventoryEntry(
            rule_id=rule.rule_id,
            rule_version=rule.rule_version,
            rule_lifecycle=rule.lifecycle.value,
            severity=rule.severity.value,
            adversary_class=(
                rule.adversary_class.value if rule.adversary_class is not None else None
            ),
        )
        for rule in sorted(get_production_rules(), key=lambda item: item.rule_id)
    )
    semgrep_rules = get_semgrep_rule_inventory()
    semgrep_version = get_semgrep_version()
    semgrep_rule_sources = get_semgrep_rule_source_digests()

    payload = _fingerprint_payload(
        inhouse_rules=inhouse_rules,
        semgrep_rules=semgrep_rules,
        semgrep_version=semgrep_version,
        semgrep_rule_sources=semgrep_rule_sources,
    )
    fingerprint = hashlib.sha256(_canonical_json(payload)).hexdigest()
    return StaticRuleBundleInventory(
        schema_version=RULE_BUNDLE_FINGERPRINT_SCHEMA_VERSION,
        inhouse_rules=inhouse_rules,
        semgrep_rules=semgrep_rules,
        semgrep_version=semgrep_version,
        semgrep_rule_sources=semgrep_rule_sources,
        rules_bundle_fingerprint=fingerprint,
    )


def _fingerprint_payload(
    *,
    inhouse_rules: tuple[InhouseRuleInventoryEntry, ...],
    semgrep_rules: tuple[SemgrepRuleInventoryEntry, ...],
    semgrep_version: str,
    semgrep_rule_sources: tuple[tuple[str, str], ...],
) -> dict[str, object]:
    return {
        "schema_version": RULE_BUNDLE_FINGERPRINT_SCHEMA_VERSION,
        "inhouse_rules": [asdict(entry) for entry in inhouse_rules],
        "semgrep_rules": [asdict(entry) for entry in semgrep_rules],
        "semgrep_version": semgrep_version,
        "semgrep_rule_sources": [
            {"relative_path": path, "sha256": digest}
            for path, digest in semgrep_rule_sources
        ],
    }


def _canonical_json(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


__all__ = [
    "RULE_BUNDLE_FINGERPRINT_SCHEMA_VERSION",
    "InhouseRuleInventoryEntry",
    "StaticRuleBundleInventory",
    "build_rule_bundle_inventory",
]
