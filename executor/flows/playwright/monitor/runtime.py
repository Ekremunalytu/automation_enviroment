"""Runtime verification and process helpers for activation monitoring."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..health import (
    build_run_quality,
    count_target_activations,
    derive_verified_capabilities,
    is_background_activation,
    reconcile_coverage_verification,
)
from ..runtime_capture._shared import _log
from ..runtime_capture.events import ActivationEntry
from .records import EventAttemptRecord, PrerequisiteResult
from .support import resolve_monitor_api

if TYPE_CHECKING:
    from .types import ActivationReport


def _trigger_item_as_dict(item: Any) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        return dict(item)

    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, dict):
            return dumped

    dict_method = getattr(item, "dict", None)
    if callable(dict_method):
        dumped = dict_method()
        if isinstance(dumped, dict):
            return dumped

    return None


@dataclass(frozen=True)
class _ProcessEntry:
    pid: int
    ppid: int
    args: str


_EXCLUDED_EXTENSION_HOST_SIGNATURES = (
    "server.bundle.js",
    "jsonservermain",
    "tsserver.js",
    "typingsinstaller.js",
    "htmlservermain",
    "cssservermain",
    "python-env-tools",
    "shellintegration",
)


def _parse_process_table(output: str) -> list[_ProcessEntry]:
    entries: list[_ProcessEntry] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        entries.append(_ProcessEntry(pid=pid, ppid=ppid, args=parts[2]))
    return entries


def _extract_user_data_dir(args: str) -> str:
    match = re.search(r"--user-data-dir(?:=|\s+)(\S+)", args)
    return match.group(1).strip() if match else ""


def _is_excluded_extension_host_candidate(args: str) -> bool:
    lowered = args.lower()
    return any(
        signature in lowered for signature in _EXCLUDED_EXTENSION_HOST_SIGNATURES
    )


def _find_vscode_main_pid(
    entries: list[_ProcessEntry],
    user_data_dir: str,
) -> int | None:
    candidates = [
        entry
        for entry in entries
        if "/usr/share/code/code" in entry.args and "--type=" not in entry.args
    ]
    if user_data_dir:
        narrowed = [
            entry
            for entry in candidates
            if _extract_user_data_dir(entry.args) == user_data_dir
        ]
        if narrowed:
            candidates = narrowed
    if not candidates:
        return None
    return max(candidates, key=lambda entry: entry.pid).pid


def _score_extension_host_candidate(
    candidate: _ProcessEntry,
    entries: list[_ProcessEntry],
    vscode_main_pid: int | None,
) -> tuple[int, int, int]:
    child_score = (
        4 if vscode_main_pid is not None and candidate.ppid == vscode_main_pid else 0
    )
    referenced_by_children = sum(
        1 for entry in entries if f"--clientProcessId={candidate.pid}" in entry.args
    )
    inspector_score = (
        1
        if (
            "--inspect-port" in candidate.args
            or "--experimental-network-inspection" in candidate.args
        )
        else 0
    )
    return (
        child_score + referenced_by_children + inspector_score,
        referenced_by_children,
        candidate.pid,
    )


def _select_extension_host_pid(entries: list[_ProcessEntry]) -> int | None:
    legacy_candidates = [
        entry for entry in entries if "extensionhost" in entry.args.lower()
    ]
    if legacy_candidates:
        return max(legacy_candidates, key=lambda entry: entry.pid).pid

    code_entries = [
        entry
        for entry in entries
        if "--type=utility" in entry.args
        and "--utility-sub-type=node.mojom.NodeService" in entry.args
    ]
    if not code_entries:
        return None

    user_data_dir = ""
    for entry in code_entries:
        user_data_dir = _extract_user_data_dir(entry.args)
        if user_data_dir:
            break
    vscode_main_pid = _find_vscode_main_pid(entries, user_data_dir)
    filtered = [
        entry
        for entry in code_entries
        if (not user_data_dir or _extract_user_data_dir(entry.args) == user_data_dir)
        and not _is_excluded_extension_host_candidate(entry.args)
    ]
    if not filtered:
        return None
    return max(
        filtered,
        key=lambda entry: _score_extension_host_candidate(
            entry,
            entries,
            vscode_main_pid,
        ),
    ).pid


def _find_extension_host_pid() -> int | None:
    try:
        # arch-allow: bare-binary-path  # W8-4-followup: see POST_POC_BACKLOG.md
        result = subprocess.run(  # nosec B603
            ["ps", "-eo", "pid=,ppid=,args="],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        _log(f"Failed to inspect process table: {exc}")
        return None

    return _select_extension_host_pid(_parse_process_table(result.stdout))


def _wait_for_extension_host_pid(
    *,
    timeout_s: float = 10.0,
    poll_interval_s: float = 0.5,
) -> tuple[int | None, dict[str, Any]]:
    api = resolve_monitor_api()
    deadline = api.time.monotonic() + timeout_s
    attempts = 0
    while True:
        attempts += 1
        pid = api._find_extension_host_pid()
        if pid is not None:
            return (
                pid,
                {
                    "attempts": attempts,
                    "selected_pid": pid,
                    "status": "resolved",
                    "poll_timeout_s": timeout_s,
                    "poll_interval_s": poll_interval_s,
                    "failure_reason": "",
                },
            )
        if api.time.monotonic() >= deadline:
            return (
                None,
                {
                    "attempts": attempts,
                    "selected_pid": None,
                    "status": "not_found",
                    "poll_timeout_s": timeout_s,
                    "poll_interval_s": poll_interval_s,
                    "failure_reason": "Extension Host PID not found during attach window.",
                },
            )
        api.time.sleep(poll_interval_s)


def _merge_activation_entries(
    existing: list[ActivationEntry],
    new_entries: list[ActivationEntry],
) -> list[ActivationEntry]:
    merged = list(existing)
    seen = {
        (
            entry.extension_id,
            entry.activation_event,
            entry.timestamp,
            entry.duration_ms,
        )
        for entry in existing
    }

    for entry in new_entries:
        dedup_key = (
            entry.extension_id,
            entry.activation_event,
            entry.timestamp,
            entry.duration_ms,
        )
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        merged.append(entry)

    return merged


def _requires_startup_grace(report: ActivationReport) -> bool:
    if not report.target_extension_id or report.target_extension_observed:
        return False

    for attempt in report.event_attempts:
        is_official_track = str(getattr(attempt, "track", "official")) == "official"
        is_official_flag = bool(getattr(attempt, "official", True))
        is_heuristic = bool(getattr(attempt, "heuristic", False))
        is_official = is_official_track or (is_official_flag and not is_heuristic)
        if not is_official:
            continue

        activation_event = str(getattr(attempt, "activation_event", "")).strip()
        declared_event = str(getattr(attempt, "declared_event", "")).strip()
        if activation_event in {"onStartupFinished", "*"}:
            return True
        if declared_event in {"onStartupFinished", "*"}:
            return True

    return False


def _build_scenario_log_message(
    action: str,
    name: str,
    status: str,
    metadata: dict[str, Any] | None,
) -> str:
    label = name.replace("_", " ")
    intent = ""
    if metadata is not None:
        intent = str(metadata.get("intent", "")).strip()
    if action == "start":
        return f"Started scenario {label}" + (f": {intent}" if intent else "")
    if action == "end":
        verb = "Completed" if status != "failed" else "Failed"
        return f"{verb} scenario {label}" + (f": {intent}" if intent else "")
    return f"Scenario {label}"


def _build_stimulus_pass_log_message(
    action: str,
    label: str,
    status: str,
) -> str:
    verb = "Started" if action == "start" else "Finished"
    return f"{verb} {label} ({status})"


def _build_prerequisite_log_message(result: PrerequisiteResult) -> str:
    message = f"Prerequisite {result.label or result.key} {result.status}"
    if result.reason_code:
        message += f" ({result.reason_code})"
    return message


def _build_event_attempt_log_message(attempt: EventAttemptRecord) -> str:
    outcome = attempt.status or attempt.verification_status or "unknown"
    return (
        f"Event attempt {attempt.activation_event or attempt.event_family} "
        f"finished as {outcome}"
    )


def _build_activation_log_message(entry: ActivationEntry) -> str:
    parts = [f"Activated {entry.extension_id}"]
    if entry.activation_event:
        parts.append(f"via {entry.activation_event}")
    if entry.duration_ms is not None:
        parts.append(f"in {entry.duration_ms}ms")
    return " ".join(parts)


def _find_event_attempt(
    report: ActivationReport,
    attempt_id: str,
) -> EventAttemptRecord | None:
    for attempt in report.event_attempts:
        if attempt.attempt_id == attempt_id:
            return attempt
    return None


def _entry_is_supported(entry: Mapping[str, Any]) -> bool:
    return (
        str(entry.get("support_status", entry.get("status", "unknown"))).strip()
        == "covered"
    )


def _matrix_entries_for_track(
    report: ActivationReport,
    track: str,
) -> list[dict[str, Any]]:
    coverage_tracks = getattr(report, "coverage_tracks", {}) or {}
    if track == "official":
        track_data = coverage_tracks.get("official", {})
        if isinstance(track_data, Mapping) and isinstance(
            track_data.get("matrix"),
            list,
        ):
            return list(track_data["matrix"])
        matrix = getattr(report, "coverage_matrix", [])
        return list(matrix) if isinstance(matrix, list) else []
    track_data = coverage_tracks.get(track, {})
    if isinstance(track_data, Mapping) and isinstance(track_data.get("matrix"), list):
        return list(track_data["matrix"])
    return []


def _filter_supported_capabilities(
    capabilities: list[str],
    matrix_entries: list[dict[str, Any]],
) -> list[str]:
    unique_caps = sorted({str(cap).strip() for cap in capabilities if str(cap).strip()})
    if not matrix_entries:
        return unique_caps
    supported = {
        str(entry.get("capability", "")).strip()
        for entry in matrix_entries
        if str(entry.get("capability", "")).strip() and _entry_is_supported(entry)
    }
    return sorted(capability for capability in unique_caps if capability in supported)


def _derive_runtime_attempted_capabilities(
    report: ActivationReport,
    *,
    track: str,
) -> list[str]:
    matrix_entries = _matrix_entries_for_track(report, track)
    supported = {
        str(entry.get("capability", "")).strip()
        for entry in matrix_entries
        if str(entry.get("capability", "")).strip() and _entry_is_supported(entry)
    }
    derived: set[str] = set()
    saw_runtime_attempt = False
    for attempt in getattr(report, "event_attempts", []) or []:
        if str(getattr(attempt, "track", "")).strip() != track:
            continue
        if str(getattr(attempt, "status", "")).strip() not in {
            "verified",
            "attempted_only",
            "failed",
        }:
            continue
        attempted_passes = [
            str(pass_name).strip()
            for pass_name in getattr(attempt, "attempted_passes", []) or []
            if str(pass_name).strip()
        ]
        if not attempted_passes:
            continue
        saw_runtime_attempt = True
        for capability in getattr(attempt, "capability_tags", []) or []:
            cap = str(capability).strip()
            if cap and (not supported or cap in supported):
                derived.add(cap)

    if saw_runtime_attempt:
        return sorted(derived)
    if getattr(report, "event_attempts", []):
        return []
    if track == "official":
        return list(getattr(report, "official_attempted_capabilities", []))
    return list(getattr(report, "supported_heuristic_attempted_capabilities", []))


def _derive_runtime_verified_capabilities(
    report: ActivationReport,
    *,
    track: str,
) -> list[str]:
    matrix_entries = _matrix_entries_for_track(report, track)
    supported = {
        str(entry.get("capability", "")).strip()
        for entry in matrix_entries
        if str(entry.get("capability", "")).strip() and _entry_is_supported(entry)
    }
    derived: set[str] = set()
    saw_runtime_verified = False
    for attempt in getattr(report, "event_attempts", []) or []:
        if str(getattr(attempt, "track", "")).strip() != track:
            continue
        if str(getattr(attempt, "status", "")).strip() != "verified":
            continue
        attempted_passes = [
            str(pass_name).strip()
            for pass_name in getattr(attempt, "attempted_passes", []) or []
            if str(pass_name).strip()
        ]
        if not attempted_passes:
            continue
        saw_runtime_verified = True
        for capability in getattr(attempt, "capability_tags", []) or []:
            cap = str(capability).strip()
            if cap and (not supported or cap in supported):
                derived.add(cap)

    if saw_runtime_verified:
        return sorted(derived)
    if getattr(report, "event_attempts", []):
        return []
    if track == "official":
        return _filter_supported_capabilities(
            getattr(report, "verified_capabilities", []),
            matrix_entries,
        )
    return _filter_supported_capabilities(
        getattr(report, "heuristic_verified_capabilities", []),
        matrix_entries,
    )


def _extract_official_attempted_capabilities(payload: Any) -> list[str]:
    attempted: set[str] = set()
    for entry in getattr(payload, "coverage_matrix", []) or []:
        capability = str(entry.get("capability", "")).strip()
        if (
            capability
            and (entry.get("is_active") or entry.get("selected"))
            and _entry_is_supported(entry)
        ):
            attempted.add(capability)
    for capability in getattr(payload, "official_attempted_capabilities", []) or []:
        cap = str(capability).strip()
        if cap:
            attempted.add(cap)
    return sorted(attempted)


def _extract_heuristic_attempted_capabilities(payload: Any) -> list[str]:
    attempted: set[str] = set()
    coverage_tracks = getattr(payload, "coverage_tracks", {}) or {}
    heuristic_track = coverage_tracks.get("heuristic", {})
    for entry in (
        heuristic_track.get("matrix", []) if isinstance(heuristic_track, dict) else []
    ):
        capability = str(entry.get("capability", "")).strip()
        if (
            capability
            and (entry.get("is_active") or entry.get("selected"))
            and _entry_is_supported(entry)
        ):
            attempted.add(capability)
    for capability in getattr(payload, "heuristic_attempted_capabilities", []) or []:
        cap = str(capability).strip()
        if cap:
            attempted.add(cap)
    return sorted(attempted)


def _derive_verified_capabilities(report: ActivationReport) -> list[str]:
    return derive_verified_capabilities(report)


def _count_target_activations(
    activations: list[ActivationEntry],
    target_extension_id: str,
) -> int:
    return count_target_activations(activations, target_extension_id)


def _reconcile_coverage_verification(
    report: ActivationReport,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    return reconcile_coverage_verification(report)


def _build_run_quality(report: ActivationReport) -> tuple[str, list[str]]:
    return build_run_quality(report, report.automation_health)


def _is_background_activation(activation_event: str) -> bool:
    return is_background_activation(activation_event)


def _snapshot_log_offsets() -> dict[str, int]:
    api = resolve_monitor_api()
    offsets: dict[str, int] = {}
    for log_path in api.find_exthost_logs():
        try:
            offsets[str(log_path.resolve())] = log_path.stat().st_size
        except OSError as exc:
            _log(f"Failed to snapshot {log_path}: {exc}")
    return offsets
