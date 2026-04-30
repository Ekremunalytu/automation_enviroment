"""Framework-agnostic risk-signal policy package.

Exposes the pure correlative + severity rollup logic. Runtime fact
resolvers (background-activation classifier, indexed-event helpers) are
injected by the caller (see executor/flows/playwright/signals.py for the
executor-side adapter).

Lives under ``packages/`` per ADR 0005 (charter); migrated from
``executor/flows/playwright/signal_policy.py`` in W9-2.
"""

from packages.analysis_engine.signals.policy import (
    build_risk_signals,
    build_risk_summary,
    build_signal_summary,
)

__all__ = [
    "build_risk_signals",
    "build_risk_summary",
    "build_signal_summary",
]
