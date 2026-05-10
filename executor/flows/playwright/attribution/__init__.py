"""Attribution subpackage facade.

W12-2: public surface trimmed from 29 underscore re-exports to 10 explicit
public names. The annotation, classification, and evidence-link helpers used
by the monitor collaborators (``monitor/lifecycle.py``,
``monitor/report_assembler.py``, ``monitor/scenario_accountant.py``,
``monitor/types.py``) live here under their public names; everything else
stays private inside ``events.py`` / ``links.py`` and is no longer
re-exported from the facade.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..signals import (
    build_risk_signals as _signals_build_risk_signals,
)
from ..signals import (
    build_risk_summary as _signals_build_risk_summary,
)
from ..signals import (
    build_signal_summary as _signals_build_signal_summary,
)
from .events import (
    annotate_file_events,
    annotate_network_events,
    annotate_process_events,
    format_epoch_timestamp,
    relative_time,
    scenario_name_for_timestamp,
)
from .links import build_evidence_bundle

if TYPE_CHECKING:
    from ..monitor.records import RiskSignal
    from ..monitor.types import ActivationReport


def build_risk_signals(report: ActivationReport) -> list[RiskSignal]:
    # Lazy import to break the attribution↔monitor facade cycle introduced by
    # W12-1 subpackaging (attribution loads first; monitor.records lives under
    # monitor/__init__.py which transitively re-imports attribution).
    from ..monitor.records import RiskSignal

    return _signals_build_risk_signals(report, RiskSignal)


def build_risk_summary(signals: list[RiskSignal]) -> dict[str, Any]:
    return _signals_build_risk_summary(signals)


def build_signal_summary(report: ActivationReport) -> dict[str, Any]:
    from ..health import build_run_quality

    return _signals_build_signal_summary(
        report,
        automation_health=report.automation_health,
        run_quality=build_run_quality(report, report.automation_health),
    )


__all__ = [
    "annotate_file_events",
    "annotate_network_events",
    "annotate_process_events",
    "build_evidence_bundle",
    "build_risk_signals",
    "build_risk_summary",
    "build_signal_summary",
    "format_epoch_timestamp",
    "relative_time",
    "scenario_name_for_timestamp",
]
