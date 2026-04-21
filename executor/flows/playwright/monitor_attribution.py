"""Attribution, annotation, and evidence helpers for activation monitoring."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from .monitor_records import (
        EvidenceEvent,
        EvidenceLink,
        LogStreamEntry,
        RiskSignal,
        ScenarioTrace,
    )
    from .runtime_capture._shared import _parse_iso_timestamp
    from .runtime_capture.events import (
        ActivationEntry,
        FileEvent,
        NetworkEvent,
        ProcessEvent,
    )
    from .signal_facts import (
        indexed_target_activations,
        indexed_target_file_events,
        indexed_target_network_events,
        indexed_ui_blockers,
    )
    from .signals import build_risk_signals, build_risk_summary, build_verdict
except ImportError:  # pragma: no cover - top-level executor import mode
    from monitor_records import (
        EvidenceEvent,
        EvidenceLink,
        LogStreamEntry,
        RiskSignal,
        ScenarioTrace,
    )
    from runtime_capture._shared import _parse_iso_timestamp
    from runtime_capture.events import (
        ActivationEntry,
        FileEvent,
        NetworkEvent,
        ProcessEvent,
    )
    from signal_facts import (
        indexed_target_activations,
        indexed_target_file_events,
        indexed_target_network_events,
        indexed_ui_blockers,
    )
    from signals import build_risk_signals, build_risk_summary, build_verdict

if TYPE_CHECKING:
    try:
        from .monitor_types import ActivationReport
    except ImportError:  # pragma: no cover - top-level executor import mode
        from monitor_types import ActivationReport


def _format_epoch_timestamp(epoch: float | None) -> str:
    if epoch is None or epoch <= 0:
        return ""
    from datetime import datetime

    return datetime.fromtimestamp(epoch).isoformat(timespec="milliseconds")


def _relative_time(
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


def _scenario_name_for_timestamp(
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


def _annotate_network_events(
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
        scenario_name = _scenario_name_for_timestamp(
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


def _annotate_file_events(
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


def _annotate_process_events(
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
        scenario_name = _scenario_name_for_timestamp(
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


def _build_evidence_bundle(
    report: ActivationReport,
) -> tuple[list[EvidenceEvent], list[EvidenceLink]]:
    events: list[EvidenceEvent] = []
    links: list[EvidenceLink] = list(report.evidence_links)
    monitoring_start = report.monitoring_start

    scenario_entries: list[tuple[str, ScenarioTrace]] = []
    activation_entries: list[tuple[str, ActivationEntry, float | None]] = []
    network_entries: list[tuple[str, NetworkEvent, float | None]] = []
    file_entries: list[tuple[str, FileEvent, float | None]] = []
    process_entries: list[tuple[str, ProcessEvent, float | None]] = []
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]] = []

    for index, trace in enumerate(
        sorted(report.scenario_traces, key=lambda item: item.started_at),
        start=1,
    ):
        event_id = f"scenario-{index:04d}"
        scenario_entries.append((event_id, trace))
        rel_time_s = None
        if monitoring_start > 0 and trace.started_at > 0:
            rel_time_s = round(max(trace.started_at - monitoring_start, 0.0), 3)
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="scenario",
                timestamp=_format_epoch_timestamp(trace.started_at),
                rel_time_s=rel_time_s,
                collector="automation",
                actor="automation",
                scenario_name=trace.name,
                summary=f"Scenario {trace.name} {trace.status}",
                raw_context={
                    "status": trace.status,
                    "started_at": trace.started_at,
                    "ended_at": trace.ended_at,
                },
            )
        )

    for index, activation in enumerate(report.activated, start=1):
        event_id = f"activation-{index:04d}"
        event_epoch = _resolve_event_epoch(
            activation.timestamp,
            None,
            monitoring_start,
        )
        activation_entries.append((event_id, activation, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="activation",
                timestamp=activation.timestamp or _format_epoch_timestamp(event_epoch),
                rel_time_s=round(max(event_epoch - monitoring_start, 0.0), 3)
                if event_epoch is not None and monitoring_start > 0
                else None,
                collector=activation.source or "log",
                actor="extension",
                extension_id=activation.extension_id,
                activation_event=activation.activation_event,
                summary=(
                    f"Activation {activation.extension_id}"
                    + (
                        f" via {activation.activation_event}"
                        if activation.activation_event
                        else ""
                    )
                ),
                raw_context={
                    "success": activation.success,
                    "duration_ms": activation.duration_ms,
                    "source": activation.source,
                },
            )
        )

    ui_blockers = [
        entry for entry in report.log_entries if entry.stream == "ui_blockers"
    ]
    for index, blocker in enumerate(ui_blockers, start=1):
        event_id = f"ui-blocker-{index:04d}"
        event_epoch = _resolve_event_epoch(
            blocker.timestamp,
            blocker.rel_time_s,
            monitoring_start,
        )
        blocker_entries.append((event_id, blocker, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="ui_blocker",
                timestamp=blocker.timestamp or _format_epoch_timestamp(event_epoch),
                rel_time_s=blocker.rel_time_s,
                collector=blocker.stream,
                actor="automation",
                scenario_name=blocker.scenario_name,
                activation_event=blocker.activation_event,
                summary=blocker.message,
                raw_context={
                    "status": blocker.status,
                    "stream": blocker.stream,
                },
            )
        )

    for index, network_event in enumerate(report.network_events, start=1):
        event_id = f"network-{index:04d}"
        event_epoch = _resolve_event_epoch(
            network_event.timestamp,
            network_event.rel_time_s,
            monitoring_start,
        )
        network_entries.append((event_id, network_event, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="network",
                timestamp=network_event.timestamp
                or _format_epoch_timestamp(event_epoch),
                rel_time_s=network_event.rel_time_s,
                collector="tshark",
                actor=_actor_from_network_event(network_event),
                scenario_name=_scenario_name_for_timestamp(
                    network_event.timestamp,
                    network_event.rel_time_s,
                    report.scenario_traces,
                    monitoring_start,
                ),
                extension_id=network_event.related_extension_id,
                activation_event=network_event.related_activation_event,
                protocol=network_event.protocol,
                host=network_event.host,
                destination_ip=network_event.destination_ip,
                destination_port=network_event.destination_port,
                attribution_status=network_event.attribution_status,
                attribution_basis=network_event.attribution_basis,
                attribution_confidence=network_event.attribution_confidence,
                is_target_extension_event=network_event.is_target_extension_event,
                noise_reason=network_event.noise_reason,
                summary=network_event.summary,
                raw_context={
                    "event_type": network_event.event_type,
                    "source_ip": network_event.source_ip,
                    "path": network_event.path,
                    "http_method": network_event.http_method,
                    "http_status_code": network_event.http_status_code,
                    "http_content_type": network_event.http_content_type,
                    "request_body_sha256": network_event.request_body_sha256,
                    "request_body_preview": network_event.request_body_preview,
                    "request_body_truncated": network_event.request_body_truncated,
                    "response_body_sha256": network_event.response_body_sha256,
                    "response_body_preview": network_event.response_body_preview,
                    "response_body_truncated": network_event.response_body_truncated,
                },
            )
        )

    for index, file_event in enumerate(report.file_events, start=1):
        event_id = f"file-{index:04d}"
        event_epoch = _resolve_event_epoch(
            file_event.timestamp,
            file_event.rel_time_s,
            monitoring_start,
        )
        file_entries.append((event_id, file_event, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="file",
                timestamp=file_event.timestamp or _format_epoch_timestamp(event_epoch),
                rel_time_s=file_event.rel_time_s,
                collector=file_event.observer or "unknown",
                actor=_actor_from_file_source(file_event.source),
                scenario_name=file_event.scenario_name,
                extension_id=file_event.related_extension_id,
                activation_event=file_event.related_activation_event,
                operation=file_event.operation,
                path=file_event.path,
                attribution_status=file_event.attribution_status,
                attribution_basis=file_event.attribution_basis,
                attribution_confidence=file_event.attribution_confidence,
                is_target_extension_event=file_event.is_target_extension_event,
                noise_reason=file_event.noise_reason,
                artifact_class=file_event.artifact_class,
                sensitive=file_event.sensitive,
                summary=file_event.summary,
                raw_context={
                    "secondary_path": file_event.secondary_path,
                    "flags": file_event.flags,
                    "observer": file_event.observer,
                    "source": file_event.source,
                },
            )
        )

    for index, process_event in enumerate(report.process_events, start=1):
        event_id = f"process-{index:04d}"
        event_epoch = _resolve_event_epoch(
            process_event.timestamp,
            process_event.rel_time_s,
            monitoring_start,
        )
        process_entries.append((event_id, process_event, event_epoch))
        events.append(
            EvidenceEvent(
                event_id=event_id,
                kind="process",
                timestamp=process_event.timestamp
                or _format_epoch_timestamp(event_epoch),
                rel_time_s=process_event.rel_time_s,
                collector="strace",
                actor="extension"
                if process_event.is_target_extension_event
                else "unknown",
                scenario_name=_scenario_name_for_timestamp(
                    process_event.timestamp,
                    process_event.rel_time_s,
                    report.scenario_traces,
                    monitoring_start,
                ),
                extension_id=process_event.related_extension_id,
                activation_event=process_event.related_activation_event,
                operation=process_event.operation,
                attribution_status=process_event.attribution_status,
                attribution_basis=process_event.attribution_basis,
                attribution_confidence=process_event.attribution_confidence,
                is_target_extension_event=process_event.is_target_extension_event,
                summary=process_event.summary,
                raw_context={
                    "pid": process_event.pid,
                    "ppid": process_event.ppid,
                    "command": process_event.command,
                    "arguments_preview": process_event.arguments_preview,
                    "cwd": process_event.cwd,
                },
            )
        )

    links.extend(
        _build_scenario_links(
            scenario_entries,
            activation_entries,
            network_entries,
            file_entries,
            process_entries,
            blocker_entries,
        )
    )
    links.extend(
        _build_temporal_links(
            activation_entries,
            network_entries,
            file_entries,
            process_entries,
        )
    )
    links.extend(_build_duplicate_file_links(file_entries))
    links.extend(_build_noise_links(scenario_entries, file_entries, blocker_entries))
    return events, _dedupe_evidence_links(links)


def _build_scenario_links(
    scenario_entries: list[tuple[str, ScenarioTrace]],
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    network_entries: list[tuple[str, NetworkEvent, float | None]],
    file_entries: list[tuple[str, FileEvent, float | None]],
    process_entries: list[tuple[str, ProcessEvent, float | None]],
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for scenario_event_id, trace in scenario_entries:
        window_end = trace.ended_at or trace.started_at
        if trace.started_at <= 0 or window_end <= 0:
            continue
        for event_id, _, event_epoch in [
            *activation_entries,
            *network_entries,
            *file_entries,
            *process_entries,
            *blocker_entries,
        ]:
            if event_epoch is None:
                continue
            if trace.started_at <= event_epoch <= window_end:
                links.append(
                    EvidenceLink(
                        from_event_id=event_id,
                        to_event_id=scenario_event_id,
                        link_type="occurred_in_scenario",
                        confidence=1.0,
                        reason=f"Event happened during scenario window {trace.name}.",
                    )
                )
    return links


def _build_temporal_links(
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    network_entries: list[tuple[str, NetworkEvent, float | None]],
    file_entries: list[tuple[str, FileEvent, float | None]],
    process_entries: list[tuple[str, ProcessEvent, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for event_id, file_event, event_epoch in file_entries:
        if event_epoch is None:
            continue
        activation_match = _nearest_activation(activation_entries, event_epoch)
        if activation_match is None:
            continue
        activation_event_id, _activation_entry, delta = activation_match
        if file_event.is_target_extension_event:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="caused_by_target_extension",
                    confidence=file_event.attribution_confidence
                    or _temporal_confidence(delta),
                    reason=(
                        "File activity is attributed to the target extension because the "
                        "extension-host event aligned with its activation window."
                    ),
                )
            )
        elif file_event.attribution_status in {"competing_candidate", "unattributed"}:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="near_target_activation",
                    confidence=_temporal_confidence(delta),
                    reason=(
                        "File activity happened near the target activation but ownership "
                        f"remains unconfirmed ({delta:.3f}s delta)."
                    ),
                )
            )

    for event_id, network_event, event_epoch in network_entries:
        if event_epoch is None:
            continue
        activation_match = _nearest_activation(activation_entries, event_epoch)
        if activation_match is None:
            continue
        activation_event_id, _activation_entry, delta = activation_match
        if network_event.is_target_extension_event:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="caused_by_target_extension",
                    confidence=network_event.attribution_confidence
                    or _temporal_confidence(delta),
                    reason=(
                        "Network activity is attributed to the target extension because it "
                        "followed a target activation without a competing activation."
                    ),
                )
            )
        elif network_event.attribution_status in {
            "near_target_activation",
            "competing_candidate",
        }:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="near_target_activation",
                    confidence=_temporal_confidence(delta),
                    reason=(
                        "Network activity happened near the target activation but remains "
                        f"correlative only ({delta:.3f}s delta)."
                    ),
                )
            )
    for event_id, process_event, event_epoch in process_entries:
        if event_epoch is None:
            continue
        activation_match = _nearest_activation(activation_entries, event_epoch)
        if activation_match is None:
            continue
        activation_event_id, _activation_entry, delta = activation_match
        if process_event.is_target_extension_event:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="caused_by_target_extension",
                    confidence=process_event.attribution_confidence
                    or _temporal_confidence(delta),
                    reason=(
                        "Process activity is attributed to the target extension because "
                        "it aligned with a target activation window in the Extension Host tree."
                    ),
                )
            )
        elif process_event.attribution_status in {
            "near_target_activation",
            "competing_candidate",
            "unattributed",
        }:
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=activation_event_id,
                    link_type="near_target_activation",
                    confidence=_temporal_confidence(delta),
                    reason=(
                        "Process activity happened near the target activation but "
                        f"ownership remains unconfirmed ({delta:.3f}s delta)."
                    ),
                )
            )
    return links


def _build_duplicate_file_links(
    file_entries: list[tuple[str, FileEvent, float | None]],
) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for index, (left_id, left_event, left_epoch) in enumerate(file_entries):
        for right_id, right_event, right_epoch in file_entries[index + 1 :]:
            if left_event.path != right_event.path:
                continue
            if left_event.operation != right_event.operation:
                continue
            if left_event.observer == right_event.observer:
                continue
            if {left_event.observer, right_event.observer} != {"strace", "inotify"}:
                continue

            if (
                left_epoch is not None
                and right_epoch is not None
                and abs(left_epoch - right_epoch) > 1.0
            ):
                continue

            links.append(
                EvidenceLink(
                    from_event_id=left_id,
                    to_event_id=right_id,
                    link_type="duplicate_signal",
                    confidence=0.9,
                    reason=(
                        "Both strace and inotify observed the same file artifact "
                        "operation within the same investigation window."
                    ),
                )
            )
    return links


def _build_noise_links(
    scenario_entries: list[tuple[str, ScenarioTrace]],
    file_entries: list[tuple[str, FileEvent, float | None]],
    blocker_entries: list[tuple[str, LogStreamEntry, float | None]],
) -> list[EvidenceLink]:
    scenario_ids = {trace.name: event_id for event_id, trace in scenario_entries}
    links: list[EvidenceLink] = []
    for event_id, file_event, _ in file_entries:
        scenario_event_id = scenario_ids.get(file_event.scenario_name)
        if scenario_event_id is None:
            continue
        if file_event.attribution_status == "automation_noise":
            links.append(
                EvidenceLink(
                    from_event_id=event_id,
                    to_event_id=scenario_event_id,
                    link_type="automation_noise",
                    confidence=1.0,
                    reason=(
                        "This inotify file event belongs to the automation scenario rather "
                        "than extension-host ownership."
                    ),
                )
            )
    for event_id, blocker_entry, _ in blocker_entries:
        scenario_event_id = scenario_ids.get(blocker_entry.scenario_name)
        if scenario_event_id is None:
            continue
        links.append(
            EvidenceLink(
                from_event_id=event_id,
                to_event_id=scenario_event_id,
                link_type="blocked_by_ui",
                confidence=1.0,
                reason="A VS Code popup or modal interfered with the active automation flow.",
            )
        )
    return links


def _nearest_activation(
    activation_entries: list[tuple[str, ActivationEntry, float | None]],
    event_epoch: float,
) -> tuple[str, ActivationEntry, float] | None:
    nearest: tuple[str, ActivationEntry, float] | None = None
    for activation_event_id, activation_entry, activation_epoch in activation_entries:
        if activation_epoch is None:
            continue
        delta = abs(event_epoch - activation_epoch)
        if delta > 5.0:
            continue
        if nearest is None or delta < nearest[2]:
            nearest = (activation_event_id, activation_entry, delta)
    return nearest


def _temporal_confidence(delta: float) -> float:
    return max(0.2, round(0.7 - min(delta, 5.0) * 0.1, 2))


def _dedupe_evidence_links(links: list[EvidenceLink]) -> list[EvidenceLink]:
    deduped: list[EvidenceLink] = []
    seen: set[tuple[str, str, str, str]] = set()
    for link in links:
        key = (
            link.from_event_id,
            link.to_event_id,
            link.link_type,
            link.reason,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(link)
    return deduped


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
    return build_risk_signals(report, RiskSignal)


def _build_risk_summary(signals: list[RiskSignal]) -> dict[str, Any]:
    return build_risk_summary(signals)


def _build_verdict(report: ActivationReport) -> dict[str, Any]:
    try:
        from .health import build_run_quality
    except ImportError:  # pragma: no cover - top-level executor import mode
        from health import build_run_quality

    return build_verdict(
        report,
        automation_health=report.automation_health,
        run_quality=build_run_quality(report, report.automation_health),
    )


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
