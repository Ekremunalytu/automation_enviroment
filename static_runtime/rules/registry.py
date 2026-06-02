"""In-memory registry of in-house static rules (ES-3a, ADR 0016).

Mirror of ``packages.analysis_engine.rules.registry``: rules self-register at
import time; the builtins are imported lazily on first lookup so importing the
package does not force every rule module to load.
"""

from __future__ import annotations

import importlib

from packages.analysis_contracts.detection.enums import RuleLifecycle
from static_runtime.rules.base import StaticRule

_REGISTRY: dict[str, StaticRule] = {}
_BUILTIN_STATIC_RULE_MODULES = (
    "static_runtime.rules.s1_manifest_red_flags",
    "static_runtime.rules.s2_typosquat_static",
    "static_runtime.rules.s3_file_tree_heuristics",
    "static_runtime.rules.s4_blacklisted_domain",
    "static_runtime.rules.s5_network_indicators",
    "static_runtime.rules.s6_obfuscation_indicators",
    "static_runtime.rules.s7_secret_exposure",
)
_BUILTINS_LOADED = False


def register(rule: StaticRule) -> None:
    """Register a static rule by its stable rule_id."""
    _REGISTRY[rule.rule_id] = rule


def get_production_rules() -> list[StaticRule]:
    """Return rules eligible to contribute to the static pre-check report."""
    _ensure_builtin_rules_loaded()
    return [
        rule
        for rule in _REGISTRY.values()
        if rule.lifecycle == RuleLifecycle.PRODUCTION
    ]


def get_all_rules() -> list[StaticRule]:
    """Return all registered static rules."""
    _ensure_builtin_rules_loaded()
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Reset the registry for isolated tests."""
    _REGISTRY.clear()


def _ensure_builtin_rules_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    for module_name in _BUILTIN_STATIC_RULE_MODULES:
        importlib.import_module(module_name)
    _BUILTINS_LOADED = True


__all__ = ["clear_registry", "get_all_rules", "get_production_rules", "register"]
