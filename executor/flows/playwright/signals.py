"""Helpers for risk signals and verdict policy."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

try:
    from .signal_policy import build_risk_signals, build_risk_summary, build_verdict
except ImportError:  # pragma: no cover - top-level executor import mode
    from signal_policy import build_risk_signals, build_risk_summary, build_verdict

__all__ = [
    "build_risk_signals",
    "build_risk_summary",
    "build_verdict",
]
