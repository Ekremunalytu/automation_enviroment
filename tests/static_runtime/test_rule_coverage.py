"""Registry coverage contract for the in-house static rules.

Static-side mirror of ``tests/security/test_rule_coverage.py``: pins the exact
production rule-id set so dropping or renaming a rule in
``_BUILTIN_STATIC_RULE_MODULES`` is caught here rather than only by a downstream
rule-specific test (which is flakier to attribute). Also guards that every rule
the registry surfaces is PRODUCTION lifecycle.
"""

from __future__ import annotations

from packages.analysis_contracts.detection import RuleLifecycle
from static_runtime.rules.registry import get_production_rules

EXPECTED_STATIC_PRODUCTION_RULE_IDS = {
    "extrace.s1.activation_wildcard",
    "extrace.s1.suspicious_capabilities",
    "extrace.s1.generic_publisher",
    "extrace.s2.typosquat",
    "extrace.s3.embedded_native_binary",
    "extrace.s3.unusual_file_signature",
    "extrace.s4.blacklisted_domain",
    "extrace.s5.suspicious_network_endpoint",
    "extrace.s6.obfuscation_indicators",
    "extrace.s7.hardcoded_secret",
    "extrace.s8.exfil_webhook",
    "extrace.s9.crypto_address_scan",
    "extrace.s10.reverse_shell",
    "extrace.s11.download_cradle",
    "extrace.s12.invisible_unicode_run",
    "extrace.s13.native_node_loader",
    "extrace.s14.globalstate_dormancy",
}


def test_get_production_rules_returns_the_expected_static_set() -> None:
    rule_ids = {rule.rule_id for rule in get_production_rules()}
    assert rule_ids == EXPECTED_STATIC_PRODUCTION_RULE_IDS, (
        f"static production rule registry drifted: got {sorted(rule_ids)}"
    )


def test_every_static_rule_is_marked_production_lifecycle() -> None:
    for rule in get_production_rules():
        assert rule.lifecycle == RuleLifecycle.PRODUCTION, (
            f"{rule.rule_id} surfaced by get_production_rules but "
            f"lifecycle={rule.lifecycle}"
        )


def test_blacklist_domain_rule_is_high_but_not_a_critical_blocker() -> None:
    """The s4 blacklist rule warns (HIGH) — it is never CRITICAL (would BLOCK)."""
    rules = {rule.rule_id: rule for rule in get_production_rules()}
    s4 = rules["extrace.s4.blacklisted_domain"]
    assert s4.severity.value == "high"
