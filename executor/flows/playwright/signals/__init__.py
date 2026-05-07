"""Executor-side risk-signal facade.

Wraps the framework-agnostic policy in
``packages.analysis_engine.signals.policy`` with executor-local fact
resolvers (``signal_facts.indexed_*``) and the activation classifier
(``health.is_background_activation``). Migrated from ``signal_policy.py``
in W9-2 per ADR 0008 / ADR 0005.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import Any

from packages.analysis_engine.signals.policy import (
    build_risk_signals as _build_risk_signals_policy,
)
from packages.analysis_engine.signals.policy import (
    build_risk_summary,
)
from packages.analysis_engine.signals.policy import (
    build_signal_summary as _build_signal_summary_policy,
)

from ..health import is_background_activation
from .facts import (
    indexed_target_activations,
    indexed_target_file_events,
    indexed_target_network_events,
    indexed_ui_blockers,
)


def build_risk_signals(report: Any, risk_signal_type: Any) -> list[Any]:
    return _build_risk_signals_policy(
        report,
        risk_signal_type,
        is_background_activation=is_background_activation,
        indexed_target_activations=indexed_target_activations,
        indexed_target_file_events=indexed_target_file_events,
        indexed_target_network_events=indexed_target_network_events,
        indexed_ui_blockers=indexed_ui_blockers,
    )


def build_signal_summary(
    report: Any,
    *,
    automation_health: dict[str, Any],
    run_quality: tuple[str, list[str]],
) -> dict[str, Any]:
    return _build_signal_summary_policy(
        report,
        automation_health=automation_health,
        run_quality=run_quality,
        is_background_activation=is_background_activation,
    )


__all__ = [
    "build_risk_signals",
    "build_risk_summary",
    "build_signal_summary",
]
