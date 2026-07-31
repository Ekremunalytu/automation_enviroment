"""Deterministic live rule identity and bundle fingerprint for SMF-0.

The live registries provide identity and lifecycle fields. Small reviewed
metadata completes capability, artifact-role, test-ownership, known limitation,
runtime-budget, and gate-effect fields in the same machine-readable artifact.
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
_INHOUSE_TEST_MODULES = {
    "s1": "tests/static_runtime/test_s1_manifest_red_flags.py",
    "s2": "tests/static_runtime/test_s2_typosquat_static.py",
    "s3": "tests/static_runtime/test_s3_file_tree_heuristics.py",
    "s4": "tests/static_runtime/test_s4_blacklisted_domain.py",
    "s5": "tests/static_runtime/test_s5_network_indicators.py",
    "s6": "tests/static_runtime/test_s6_obfuscation_indicators.py",
    "s7": "tests/static_runtime/test_s7_secret_exposure.py",
    "s8": "tests/static_runtime/test_s8_exfil_webhook.py",
    "s9": "tests/static_runtime/test_s9_crypto_address_scan.py",
    "s10": "tests/static_runtime/test_s10_reverse_shell.py",
    "s11": "tests/static_runtime/test_s11_download_cradle.py",
    "s12": "tests/static_runtime/test_s12_invisible_unicode.py",
    "s13": "tests/static_runtime/test_s13_native_node_loader.py",
    "s14": "tests/static_runtime/test_s14_globalstate_dormancy.py",
    "s15": "tests/static_runtime/test_s15_path_traversal_server.py",
    "s16": "tests/static_runtime/test_s16_cross_extension_tamper.py",
    "s17": "tests/static_runtime/test_s17_credential_exfil.py",
    "s18": "tests/static_runtime/test_s18_download_exec_dropper.py",
    "s19": "tests/static_runtime/test_s19_stylesheet_threats.py",
    "s20": "tests/static_runtime/test_s20_rmm_remote_access.py",
}


@dataclass(frozen=True, slots=True)
class InhouseRuleInventoryEntry:
    """Code-derived identity fields for one production in-house rule."""

    rule_id: str
    rule_version: str
    rule_lifecycle: str
    severity: str
    adversary_class: str | None
    capabilities: tuple[str, ...]
    gate_effect: str
    artifact_roles: tuple[str, ...]
    test_ownership: tuple[str, ...]
    positive_tests: tuple[str, ...]
    negative_tests: tuple[str, ...]
    known_false_positives: tuple[str, ...]
    known_blind_spots: tuple[str, ...]
    runtime_budget: str
    owner: str


@dataclass(frozen=True, slots=True)
class RuleReviewMetadata:
    capabilities: tuple[str, ...]
    gate_effect: str
    artifact_roles: tuple[str, ...]
    test_ownership: tuple[str, ...]
    positive_tests: tuple[str, ...]
    negative_tests: tuple[str, ...]
    known_false_positives: tuple[str, ...]
    known_blind_spots: tuple[str, ...]
    runtime_budget: str
    owner: str


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

    inhouse_entries: list[InhouseRuleInventoryEntry] = []
    for rule in sorted(get_production_rules(), key=lambda item: item.rule_id):
        review = _review_metadata(rule.rule_id, rule.severity.value)
        inhouse_entries.append(
            InhouseRuleInventoryEntry(
                rule_id=rule.rule_id,
                rule_version=rule.rule_version,
                rule_lifecycle=rule.lifecycle.value,
                severity=rule.severity.value,
                adversary_class=(
                    rule.adversary_class.value
                    if rule.adversary_class is not None
                    else None
                ),
                capabilities=review.capabilities,
                gate_effect=review.gate_effect,
                artifact_roles=review.artifact_roles,
                test_ownership=review.test_ownership,
                positive_tests=review.positive_tests,
                negative_tests=review.negative_tests,
                known_false_positives=review.known_false_positives,
                known_blind_spots=review.known_blind_spots,
                runtime_budget=review.runtime_budget,
                owner=review.owner,
            )
        )
    inhouse_rules = tuple(inhouse_entries)
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


def _review_metadata(rule_id: str, severity: str) -> RuleReviewMetadata:
    """Return bounded reviewed metadata shared by the machine inventory artifact."""

    family = rule_id.split(".", 2)[1]
    artifact_roles: tuple[str, ...]
    if family in {"s1", "s2"}:
        artifact_roles = ("manifest",)
    elif family == "s3":
        artifact_roles = ("binary_file", "source_file")
    elif family == "s19":
        artifact_roles = ("stylesheet",)
    else:
        artifact_roles = ("source_file",)

    known_false_positives: tuple[str, ...] = ()
    if family == "s3":
        known_false_positives = (
            "Binary-signature heuristics can classify media or database assets.",
        )
    elif family in {"s4", "s5"}:
        known_false_positives = (
            "Documentation, license, and changelog URLs can look like "
            "runtime endpoints.",
        )
    elif family in {"s6", "s12"}:
        known_false_positives = (
            "Localization, minification, and generated code can resemble obfuscation.",
        )

    gate_effect = (
        "block"
        if severity == "critical" or rule_id == "extrace.s2.typosquat"
        else "warn"
    )
    test_module = _INHOUSE_TEST_MODULES[family]
    return RuleReviewMetadata(
        capabilities=(rule_id.rsplit(".", 1)[-1],),
        gate_effect=gate_effect,
        artifact_roles=artifact_roles,
        test_ownership=(test_module,),
        positive_tests=(test_module,),
        negative_tests=(test_module,),
        known_false_positives=known_false_positives,
        known_blind_spots=(
            "Bounded text heads, unsupported formats, and runtime-computed payloads.",
        ),
        runtime_budget="cooperative shared static-analysis timeout",
        owner="security-detection",
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


def rule_inventory_payload(inventory: StaticRuleBundleInventory) -> dict[str, object]:
    """Serialize the reviewed inventory without relying on dataclass repr output."""

    return asdict(inventory)


__all__ = [
    "RULE_BUNDLE_FINGERPRINT_SCHEMA_VERSION",
    "InhouseRuleInventoryEntry",
    "RuleReviewMetadata",
    "StaticRuleBundleInventory",
    "build_rule_bundle_inventory",
    "rule_inventory_payload",
]
