"""Public control boundary for the static-analyzer container (ES-2, ADR 0016)."""

from __future__ import annotations

from dataclasses import dataclass

from executor.static_host import StaticAnalyzerError
from executor.static_host import (
    run_static_analysis_in_container as _run_static_analysis_in_container,
)


@dataclass(slots=True)
class StaticAnalyzerControl:
    """Single public surface for driving the static-analyzer container.

    Mirrors ``executor.control.ExecutorControl`` so the ES-3b orchestrator
    imports this facade rather than ``executor.static_host`` directly. Dormant
    at ES-2 (no caller until the decision-gate wiring).
    """

    def run_static_analysis(
        self,
        *,
        vsix_dir: str,
        report_path: str,
        rules_version: str,
        timeout_budget_s: int,
    ) -> str:
        return _run_static_analysis_in_container(
            vsix_dir=vsix_dir,
            report_path=report_path,
            rules_version=rules_version,
            timeout_budget_s=timeout_budget_s,
        )


default_static_analyzer_control = StaticAnalyzerControl()


__all__ = [
    "StaticAnalyzerControl",
    "StaticAnalyzerError",
    "default_static_analyzer_control",
]
