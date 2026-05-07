"""Attribution subpackage facade.

Flat re-export surface for the annotation, classification, and evidence-link
helpers that used to live in ``monitor_attribution.py``. Callers import
``_annotate_*``, ``_build_*``, and the signal-layer shims directly from this
module; the underscore-prefixed API is preserved verbatim so existing
``monitor.py`` / ``monitor_types.py`` / ``monitor_lifecycle.py`` imports keep
working after the split.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..signals import build_risk_signals, build_risk_summary, build_signal_summary
from ..signals.facts import (
    indexed_target_activations,
    indexed_target_file_events,
    indexed_target_network_events,
    indexed_ui_blockers,
)
from .events import (
    _actor_from_file_source,
    _actor_from_network_event,
    _annotate_file_events,
    _annotate_network_events,
    _annotate_process_events,
    _artifact_class_for_path,
    _classify_event_attribution,
    _format_epoch_timestamp,
    _matches_extension_signature,
    _nearest_activation_matches,
    _relative_time,
    _resolve_event_epoch,
    _scenario_name_for_timestamp,
    _upgrade_inotify_correlations,
)
from .links import (
    _build_duplicate_file_links,
    _build_evidence_bundle,
    _build_noise_links,
    _build_scenario_links,
    _build_temporal_links,
    _dedupe_evidence_links,
    _nearest_activation,
    _temporal_confidence,
)

if TYPE_CHECKING:
    from ..monitor.records import LogStreamEntry, RiskSignal
    from ..monitor.types import ActivationReport
    from ..runtime_capture.events import ActivationEntry, FileEvent, NetworkEvent


def _indexed_target_activations(
    report: ActivationReport,
) -> list[tuple[str, ActivationEntry]]:
    return indexed_target_activations(report)


def _indexed_target_file_events(
    report: ActivationReport,
) -> list[tuple[str, FileEvent]]:
    return indexed_target_file_events(report)


def _indexed_target_network_events(
    report: ActivationReport,
) -> list[tuple[str, NetworkEvent]]:
    return indexed_target_network_events(report)


def _indexed_ui_blockers(
    report: ActivationReport,
) -> list[tuple[str, LogStreamEntry]]:
    return indexed_ui_blockers(report)


def _build_risk_signals(report: ActivationReport) -> list[RiskSignal]:
    # Lazy import to break the attribution↔monitor facade cycle introduced by
    # W12-1 subpackaging (attribution loads first; monitor.records lives under
    # monitor/__init__.py which transitively re-imports attribution).
    from ..monitor.records import RiskSignal

    return build_risk_signals(report, RiskSignal)


def _build_risk_summary(signals: list[RiskSignal]) -> dict[str, Any]:
    return build_risk_summary(signals)


def _build_signal_summary(report: ActivationReport) -> dict[str, Any]:
    from ..health import build_run_quality

    return build_signal_summary(
        report,
        automation_health=report.automation_health,
        run_quality=build_run_quality(report, report.automation_health),
    )


__all__ = [
    "_actor_from_file_source",
    "_actor_from_network_event",
    "_annotate_file_events",
    "_annotate_network_events",
    "_annotate_process_events",
    "_artifact_class_for_path",
    "_build_duplicate_file_links",
    "_build_evidence_bundle",
    "_build_noise_links",
    "_build_risk_signals",
    "_build_risk_summary",
    "_build_scenario_links",
    "_build_signal_summary",
    "_build_temporal_links",
    "_classify_event_attribution",
    "_dedupe_evidence_links",
    "_format_epoch_timestamp",
    "_indexed_target_activations",
    "_indexed_target_file_events",
    "_indexed_target_network_events",
    "_indexed_ui_blockers",
    "_matches_extension_signature",
    "_nearest_activation",
    "_nearest_activation_matches",
    "_relative_time",
    "_resolve_event_epoch",
    "_scenario_name_for_timestamp",
    "_temporal_confidence",
    "_upgrade_inotify_correlations",
]
