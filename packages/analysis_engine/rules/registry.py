"""In-memory registry of detection rules."""

from __future__ import annotations

import importlib

from packages.analysis_contracts.detection import RuleLifecycle
from packages.analysis_engine.rules.base import DetectionRule

_REGISTRY: dict[str, DetectionRule] = {}
_BUILTIN_RULE_MODULES = (
    "packages.analysis_engine.rules.a1_credential_read_then_network",
    "packages.analysis_engine.rules.a2_startup_network_beacon",
    "packages.analysis_engine.rules.a3_typosquat",
    "packages.analysis_engine.rules.a4_workspace_exfil",
    "packages.analysis_engine.rules.a5_workspace_file_tamper",
    "packages.analysis_engine.rules.a6_ui_spoof",
    "packages.analysis_engine.rules.a7_blacklisted_domain",
    "packages.analysis_engine.rules.demo_runnable_canary",
)
_BUILTINS_LOADED = False


def register(rule: DetectionRule) -> None:
    """Register a rule by its stable rule_id."""

    _REGISTRY[rule.rule_id] = rule


def get_production_rules() -> list[DetectionRule]:
    """Return rules eligible to contribute to production verdicts."""

    _ensure_builtin_rules_loaded()
    return [
        rule
        for rule in _REGISTRY.values()
        if rule.lifecycle == RuleLifecycle.PRODUCTION
    ]


def get_all_rules() -> list[DetectionRule]:
    """Return all registered rules, including draft validation rules."""

    _ensure_builtin_rules_loaded()
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Reset the registry for isolated tests."""

    _REGISTRY.clear()


def _ensure_builtin_rules_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    for module_name in _BUILTIN_RULE_MODULES:
        importlib.import_module(module_name)
    _BUILTINS_LOADED = True


__all__ = ["clear_registry", "get_all_rules", "get_production_rules", "register"]
