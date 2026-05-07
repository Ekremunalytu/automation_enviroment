# ruff: noqa: F401, I001, RUF100
"""Extension Host activation monitoring facade.

This module intentionally preserves the historical flat import surface
(``monitor.ExtensionMonitor``, ``monitor.parse_tshark_event_line``,
``monitor._wait_for_extension_host_pid``, etc.) while delegating the heavy
implementation to focused sibling modules.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import time

from ..annotation import build_attribution_summary
from ..capture import summarize_extension_host_logs
from ..health import (
    build_automation_health,
    build_log_health,
    build_run_quality,
    count_target_activations,
    derive_verified_capabilities,
    is_background_activation,
    reconcile_coverage_verification,
    reconcile_event_attempts,
    summarize_event_attempts_for_report,
)
from .records import (
    EvidenceEvent,
    EvidenceLink,
    EventAttemptRecord,
    LogStreamEntry,
    PrerequisiteResult,
    RiskSignal,
    RunningExtension,
    ScenarioTrace,
    SkippedScenarioRecord,
    StimulusPassTrace,
)
from .runtime import (
    _ProcessEntry,
    _build_activation_log_message,
    _build_event_attempt_log_message,
    _build_prerequisite_log_message,
    _build_run_quality,
    _build_scenario_log_message,
    _build_stimulus_pass_log_message,
    _count_target_activations,
    _derive_runtime_attempted_capabilities,
    _derive_runtime_verified_capabilities,
    _derive_verified_capabilities,
    _extract_heuristic_attempted_capabilities,
    _extract_official_attempted_capabilities,
    _filter_supported_capabilities,
    _find_event_attempt,
    _find_extension_host_pid,
    _find_vscode_main_pid,
    _is_background_activation,
    _is_excluded_extension_host_candidate,
    _matrix_entries_for_track,
    _merge_activation_entries,
    _parse_process_table,
    _reconcile_coverage_verification,
    _requires_startup_grace,
    _score_extension_host_candidate,
    _select_extension_host_pid,
    _snapshot_log_offsets,
    _trigger_item_as_dict,
    _wait_for_extension_host_pid,
    _extract_user_data_dir,
)
from .sources import (
    find_exthost_logs,
    get_running_extensions,
    parse_activations_from_log,
    parse_activations_from_output,
    parse_all_exthost_logs,
    read_extension_host_output,
    _parse_running_extension_row,
)
from ..report_builder import build_report_data, build_summary, save_report_payload
from ..runtime_capture._shared import (  # noqa: F401 - re-exported surface
    _FILE_WATCH_PATHS,
    _NOISY_PATH_PREFIXES,
    _SENSITIVE_PATH_PREFIXES,
    VSCODE_LOGS_DIR,
    VSCODE_USER_DATA,
    _first_non_empty,
    _is_relevant_file_path,
    _is_sensitive_path,
    _log,
    _parse_iso_timestamp,
)
from ..runtime_capture.events import (
    ActivationEntry,
    FileEvent,
    NetworkEvent,
    OutputSignalEvent,
    ProcessEvent,
)
from ..runtime_capture.extension_host import (  # noqa: F401 - re-exported surface
    _ACTIVATION_PATTERNS,
    _TIMESTAMP_RE,
    ExtensionHostFileCapture,
    _activation_within_monitoring_window,
    _parse_activation_lines,
    _poll_exthost_log,
    watch_exthost_log,
)
from ..runtime_capture.filesystem import (  # noqa: F401 - re-exported surface
    _STRACE_CALL_RE,
    FileSystemCapture,
    _normalize_inotify_operation,
    _normalize_strace_operation,
    parse_inotify_file_event_line,
    parse_strace_file_event_line,
)
from ..runtime_capture.network import (  # noqa: F401 - re-exported surface
    _NETWORK_CAPTURE_FILTER,
    NetworkCapture,
    parse_tshark_event_line,
)
# NOTE (W12-2): Do NOT add `from ..signals import build_risk_signals, ...`
# back here. The historical facade exposed `monitor.build_signal_summary`
# (and the two risk siblings) via the underscore-prefixed wrappers in
# `attribution/__init__.py`, which inject `automation_health` + `run_quality`
# (and the lazy `RiskSignal` import). After the W12-2 underscore cleanup
# those wrappers are public; the lazy `__getattr__` proxy below routes
# `monitor.build_signal_summary` to `attribution.build_signal_summary`
# (the 1-arg wrapper) — re-importing the raw 3-arg signals helper here
# would shadow the proxy and crash callers that pass `(report,)` only.

# Lazy attribution re-exports (W12-1; W12-2 trimmed to public names): direct
# module-load imports for these would create a cycle (attribution.events /
# attribution.links import from ..monitor.records, which transitively triggers
# this facade's load). The PEP 562 __getattr__ below proxies access to the
# attribution subpackage without forcing it to be loaded as monitor's facade
# initializes. W12-2 trimmed the surface from 15 underscore-prefixed names to
# 10 public names; the four ``_indexed_*`` shims were dropped (callers reach
# ``signals.facts`` directly) and ``_matches_extension_signature`` /
# ``_resolve_event_epoch`` are no longer facade-public.
_LAZY_ATTRIBUTION_NAMES = (
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
)
# `.lifecycle` and `.types` both eagerly import from `..attribution`, which
# would re-enter this facade during the load triggered by attribution's
# `from ..monitor.records import ...` chain. Defer them to PEP 562 __getattr__.
_LAZY_LIFECYCLE_NAMES = ("ExtensionMonitor", "check_extension_activated")
_LAZY_TYPES_NAMES = ("ActivationReport",)


def __getattr__(name: str):
    if name in _LAZY_ATTRIBUTION_NAMES:
        from .. import attribution

        return getattr(attribution, name)
    if name in _LAZY_LIFECYCLE_NAMES:
        from . import lifecycle

        return getattr(lifecycle, name)
    if name in _LAZY_TYPES_NAMES:
        from . import types

        return getattr(types, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
