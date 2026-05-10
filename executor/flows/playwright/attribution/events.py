"""Event annotation and attribution classification for activation reports."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from datetime import datetime

from ..monitor.records import ScenarioTrace
from ..runtime_capture._shared import _parse_iso_timestamp
from ..runtime_capture.events import (
    ActivationEntry,
    FileEvent,
    NetworkEvent,
    ProcessEvent,
)


def format_epoch_timestamp(epoch: float | None) -> str:
    if epoch is None or epoch <= 0:
        return ""
    return datetime.fromtimestamp(epoch).isoformat(timespec="milliseconds")


def relative_time(
    event_epoch: float | None,
    monitoring_start: float,
) -> float | None:
    if event_epoch is None or monitoring_start <= 0:
        return None
    return round(max(event_epoch - monitoring_start, 0.0), 3)


def _resolve_event_epoch(
    timestamp: str,
    rel_time_s: float | None,
    base_time: float,
) -> float | None:
    event_epoch = _parse_iso_timestamp(timestamp)
    if event_epoch is not None:
        return event_epoch
    if rel_time_s is not None and base_time > 0:
        return base_time + rel_time_s
    return None


def _actor_from_file_source(source: str) -> str:
    if source in {"extension", "automation", "system"}:
        return source
    return "unknown"


def _actor_from_network_event(event: NetworkEvent) -> str:
    if event.is_target_extension_event:
        return "extension"
    if event.attribution_status == "near_target_activation":
        return "unknown"
    return "unknown"


def _artifact_class_for_path(path: str) -> str:
    normalized = path.strip()
    if not normalized.endswith("/package.json"):
        return ""
    if normalized.startswith("/workspace/"):
        return "workspace_runtime"
    return "manifest_ingestion"


def _nearest_activation_matches(
    event_epoch: float | None,
    activations: list[ActivationEntry],
    target_extension_id: str,
) -> tuple[tuple[ActivationEntry, float] | None, tuple[ActivationEntry, float] | None]:
    if event_epoch is None:
        return None, None

    target_match: tuple[ActivationEntry, float] | None = None
    competitor_match: tuple[ActivationEntry, float] | None = None
    for activation in activations:
        activation_epoch = _parse_iso_timestamp(activation.timestamp)
        if activation_epoch is None:
            continue
        delta = abs(event_epoch - activation_epoch)
        if delta > 5.0:
            continue
        candidate = (activation, delta)
        if activation.extension_id == target_extension_id:
            if target_match is None or delta < target_match[1]:
                target_match = candidate
            continue
        if competitor_match is None or delta < competitor_match[1]:
            competitor_match = candidate
    return target_match, competitor_match


def _classify_event_attribution(
    event_epoch: float | None,
    activations: list[ActivationEntry],
    target_extension_id: str,
    *,
    observer: str,
) -> tuple[str, str, float, str, str, bool, str]:
    if observer == "inotify":
        return (
            "automation_noise",
            "inotify captures workspace automation and system activity, not extension-host ownership",
            0.0,
            "",
            "",
            False,
            "ownership is intentionally suppressed for inotify telemetry",
        )

    if not target_extension_id or event_epoch is None:
        return (
            "unattributed",
            "target extension context was unavailable for ownership analysis",
            0.0,
            "",
            "",
            False,
            "",
        )

    target_match, competitor_match = _nearest_activation_matches(
        event_epoch,
        activations,
        target_extension_id,
    )
    if target_match is None:
        if competitor_match is not None and competitor_match[1] <= 1.25:
            competitor_id = competitor_match[0].extension_id
            return (
                "competing_candidate",
                f"nearest activation belonged to competing extension {competitor_id}",
                0.35,
                target_extension_id,
                "",
                False,
                "a different extension activated closer to this event",
            )
        return (
            "unattributed",
            "no target activation was close enough to support ownership",
            0.0,
            "",
            "",
            False,
            "",
        )

    target_activation, target_delta = target_match
    competitor_delta = competitor_match[1] if competitor_match is not None else None
    if (
        competitor_match is not None
        and competitor_delta is not None
        and competitor_delta <= min(1.25, target_delta + 0.35)
    ):
        return (
            "competing_candidate",
            "target activation overlapped with another extension activation in the same window",
            0.45,
            target_extension_id,
            target_activation.activation_event,
            False,
            f"competing activation {competitor_match[0].extension_id} was too close",
        )

    if observer == "strace":
        if target_delta <= 1.25:
            confidence = (
                0.93 if target_delta <= 0.35 else 0.84 if target_delta <= 0.75 else 0.72
            )
            return (
                "target_attributed",
                "strace event aligned tightly with the target extension activation window",
                confidence,
                target_extension_id,
                target_activation.activation_event,
                True,
                "",
            )
        return (
            "unattributed",
            "strace observed extension-host I/O but the target activation was not close enough",
            0.0,
            "",
            "",
            False,
            "",
        )

    if target_delta <= 0.75:
        confidence = 0.78 if target_delta <= 0.35 else 0.66
        return (
            "target_attributed",
            "network event happened immediately after a target activation without a competing activation",
            confidence,
            target_extension_id,
            target_activation.activation_event,
            True,
            "",
        )
    if target_delta <= 5.0:
        confidence = max(0.28, round(0.58 - min(target_delta, 5.0) * 0.06, 2))
        return (
            "near_target_activation",
            "network event was only temporally close to the target activation",
            confidence,
            target_extension_id,
            target_activation.activation_event,
            False,
            "temporal proximity alone is not treated as ownership",
        )
    return (
        "unattributed",
        "no attribution rule matched this event",
        0.0,
        "",
        "",
        False,
        "",
    )


def _upgrade_inotify_correlations(file_events: list[FileEvent]) -> list[FileEvent]:
    strace_events = [event for event in file_events if event.observer == "strace"]
    for event in file_events:
        if (
            event.observer != "inotify"
            or event.attribution_status != "automation_noise"
        ):
            continue
        event_epoch = _parse_iso_timestamp(event.timestamp)
        if event_epoch is None:
            continue
        for strace_event in strace_events:
            strace_epoch = _parse_iso_timestamp(strace_event.timestamp)
            if strace_epoch is None:
                continue
            if (
                event.path != strace_event.path
                or event.operation != strace_event.operation
            ):
                continue
            if abs(event_epoch - strace_epoch) > 1.0:
                continue
            event.attribution_status = "corroboration"
            event.attribution_basis = (
                "inotify duplicated a matching extension-host file event and is "
                "retained as corroboration only"
            )
            event.attribution_confidence = 0.25
            event.noise_reason = (
                "duplicate workspace observation; ownership remains anchored to strace"
            )
            break
    return file_events


def scenario_name_for_timestamp(
    timestamp: str,
    rel_time_s: float | None,
    scenario_traces: list[ScenarioTrace],
    monitoring_start: float,
) -> str:
    event_epoch = _resolve_event_epoch(timestamp, rel_time_s, monitoring_start)
    if event_epoch is None:
        return ""
    for trace in scenario_traces:
        if trace.started_at <= event_epoch <= (trace.ended_at or event_epoch):
            return trace.name
    return ""


def annotate_network_events(
    network_events: list[NetworkEvent],
    activations: list[ActivationEntry],
    scenario_traces: list[ScenarioTrace],
    target_extension_id: str,
) -> list[NetworkEvent]:
    annotated: list[NetworkEvent] = []
    for network_event in network_events:
        event_epoch = _resolve_event_epoch(
            network_event.timestamp,
            network_event.rel_time_s,
            0.0,
        )
        scenario_name = scenario_name_for_timestamp(
            network_event.timestamp,
            network_event.rel_time_s,
            scenario_traces,
            0.0,
        )
        (
            attribution_status,
            attribution_basis,
            attribution_confidence,
            related_extension_id,
            related_activation_event,
            is_target_extension_event,
            noise_reason,
        ) = _classify_event_attribution(
            event_epoch,
            activations,
            target_extension_id,
            observer="network",
        )
        summary = network_event.summary
        if scenario_name:
            summary = f"{summary} [{scenario_name}]"
        annotated.append(
            NetworkEvent(
                timestamp=network_event.timestamp,
                rel_time_s=network_event.rel_time_s,
                protocol=network_event.protocol,
                event_type=network_event.event_type,
                source_ip=network_event.source_ip,
                destination_ip=network_event.destination_ip,
                destination_port=network_event.destination_port,
                host=network_event.host,
                path=network_event.path,
                http_method=network_event.http_method,
                http_status_code=network_event.http_status_code,
                http_content_type=network_event.http_content_type,
                request_body_sha256=network_event.request_body_sha256,
                request_body_preview=network_event.request_body_preview,
                request_body_truncated=network_event.request_body_truncated,
                response_body_sha256=network_event.response_body_sha256,
                response_body_preview=network_event.response_body_preview,
                response_body_truncated=network_event.response_body_truncated,
                related_extension_id=related_extension_id,
                related_activation_event=related_activation_event,
                attribution_status=attribution_status,
                attribution_basis=attribution_basis,
                attribution_confidence=attribution_confidence,
                is_target_extension_event=is_target_extension_event,
                noise_reason=noise_reason,
                summary=summary,
            )
        )
    return annotated


def annotate_file_events(
    file_events: list[FileEvent],
    activations: list[ActivationEntry],
    scenario_traces: list[ScenarioTrace],
    target_extension_id: str,
) -> list[FileEvent]:
    annotated: list[FileEvent] = []
    for file_event in sorted(
        file_events,
        key=lambda entry: (
            entry.rel_time_s is None,
            entry.rel_time_s if entry.rel_time_s is not None else 0.0,
            entry.path,
        ),
    ):
        scenario_name = file_event.scenario_name
        event_epoch = _parse_iso_timestamp(file_event.timestamp)

        if event_epoch is not None and not scenario_name:
            for trace in scenario_traces:
                if (
                    trace.started_at
                    <= event_epoch
                    <= (trace.ended_at or trace.started_at)
                ):
                    scenario_name = trace.name
                    break

        source = file_event.source
        if file_event.observer == "strace":
            source = "extension"
        elif file_event.observer == "inotify" and scenario_name:
            source = "automation"
        elif file_event.observer == "inotify":
            source = "system"

        summary = file_event.summary
        if scenario_name:
            summary = f"{summary} [{scenario_name}]"
        (
            attribution_status,
            attribution_basis,
            attribution_confidence,
            related_extension_id,
            related_activation_event,
            is_target_extension_event,
            noise_reason,
        ) = _classify_event_attribution(
            event_epoch,
            activations,
            target_extension_id,
            observer=file_event.observer,
        )

        annotated.append(
            FileEvent(
                timestamp=file_event.timestamp,
                rel_time_s=file_event.rel_time_s,
                operation=file_event.operation,
                path=file_event.path,
                secondary_path=file_event.secondary_path,
                source=source,
                observer=file_event.observer,
                scenario_name=scenario_name,
                related_extension_id=related_extension_id,
                related_activation_event=related_activation_event,
                attribution_status=attribution_status,
                attribution_basis=attribution_basis,
                attribution_confidence=attribution_confidence,
                is_target_extension_event=is_target_extension_event,
                noise_reason=noise_reason,
                artifact_class=_artifact_class_for_path(file_event.path),
                flags=file_event.flags,
                sensitive=file_event.sensitive,
                summary=summary,
            )
        )

    return _upgrade_inotify_correlations(annotated)


def annotate_process_events(
    process_events: list[ProcessEvent],
    activations: list[ActivationEntry],
    scenario_traces: list[ScenarioTrace],
    target_extension_id: str,
) -> list[ProcessEvent]:
    annotated: list[ProcessEvent] = []
    for process_event in sorted(
        process_events,
        key=lambda entry: (
            entry.rel_time_s is None,
            entry.rel_time_s if entry.rel_time_s is not None else 0.0,
            entry.pid,
        ),
    ):
        event_epoch = _resolve_event_epoch(
            process_event.timestamp,
            process_event.rel_time_s,
            0.0,
        )
        (
            attribution_status,
            attribution_basis,
            attribution_confidence,
            related_extension_id,
            related_activation_event,
            is_target_extension_event,
            _noise_reason,
        ) = _classify_event_attribution(
            event_epoch,
            activations,
            target_extension_id,
            observer="strace",
        )
        summary = process_event.summary
        scenario_name = scenario_name_for_timestamp(
            process_event.timestamp,
            process_event.rel_time_s,
            scenario_traces,
            0.0,
        )
        if scenario_name:
            summary = f"{summary} [{scenario_name}]"
        annotated.append(
            ProcessEvent(
                timestamp=process_event.timestamp,
                rel_time_s=process_event.rel_time_s,
                pid=process_event.pid,
                ppid=process_event.ppid,
                operation=process_event.operation,
                command=process_event.command,
                arguments_preview=process_event.arguments_preview,
                cwd=process_event.cwd,
                related_extension_id=related_extension_id,
                related_activation_event=related_activation_event,
                attribution_status=attribution_status,
                attribution_basis=attribution_basis,
                attribution_confidence=attribution_confidence,
                is_target_extension_event=is_target_extension_event,
                summary=summary,
            )
        )
    return annotated


def _matches_extension_signature(
    file_event: FileEvent,
    extension_signatures: list[tuple[str, str, float | None]],
) -> bool:
    for path, operation, rel_time in extension_signatures:
        if path != file_event.path or operation != file_event.operation:
            continue
        if rel_time is None or file_event.rel_time_s is None:
            return True
        if abs(rel_time - file_event.rel_time_s) <= 1.0:
            return True
    return False
