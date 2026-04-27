"""Dataclasses for runtime capture events.

These are shared across network/filesystem/extension-host capture modules
and are re-exported from ``monitor`` for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActivationEntry:
    """A single extension activation event parsed from logs."""

    extension_id: str
    activation_event: str = ""
    duration_ms: int | None = None
    timestamp: str = ""
    success: bool = True
    source: str = ""  # "log", "ui", "output"
    # "" (default = activation), "activate_fn_entry", "activate_fn_exit",
    # "command_register", "provider_register". Lifecycle markers parsed
    # from exthost.log enrich event_attempts correlation in
    # health_reconciliation. Default empty preserves PR1+PR2 behavior.
    marker_type: str = ""


@dataclass
class NetworkEvent:
    """A single observed network event from tshark."""

    timestamp: str = ""
    rel_time_s: float | None = None
    protocol: str = ""
    event_type: str = ""
    source_ip: str = ""
    destination_ip: str = ""
    destination_port: int | None = None
    host: str = ""
    path: str = ""
    http_method: str = ""
    http_status_code: int | None = None
    http_content_type: str = ""
    request_body_sha256: str = ""
    request_body_preview: str = ""
    request_body_truncated: bool = False
    response_body_sha256: str = ""
    response_body_preview: str = ""
    response_body_truncated: bool = False
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    summary: str = ""


@dataclass
class FileEvent:
    """A single observed file-system event."""

    timestamp: str = ""
    rel_time_s: float | None = None
    operation: str = ""
    path: str = ""
    secondary_path: str = ""
    source: str = ""  # "extension", "automation", "system"
    observer: str = ""  # "strace", "inotify"
    scenario_name: str = ""
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    noise_reason: str = ""
    artifact_class: str = ""
    flags: str = ""
    sensitive: bool = False
    summary: str = ""


@dataclass
class ProcessEvent:
    """A single process-tree event captured from the Extension Host tree."""

    timestamp: str = ""
    rel_time_s: float | None = None
    pid: int = 0
    ppid: int | None = None
    operation: str = ""
    command: str = ""
    arguments_preview: str = ""
    cwd: str = ""
    related_extension_id: str = ""
    related_activation_event: str = ""
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    attribution_confidence: float = 0.0
    is_target_extension_event: bool = False
    summary: str = ""


@dataclass
class OutputSignalEvent:
    """A single Output channel write captured by the harness extension hook.

    PR345 PR5 + ADR 0006: emitted by the harness extension's
    createOutputChannel proxy and converted from a [extrace-harness]
    JSON-line marker by ``parse_output_signal_events``. ``channel`` is
    the OutputChannel name as passed to ``vscode.window.createOutputChannel``;
    ``text`` is the appendLine/append content truncated to 500 chars.
    Attribution is filled in post-hoc from the nearest target activation.
    """

    timestamp: str = ""
    rel_time_s: float | None = None
    channel: str = ""
    text: str = ""
    extension_id: str = ""
    activation_event: str = ""
    is_target_extension_event: bool = False
    attribution_status: str = "unattributed"
    attribution_basis: str = ""
    summary: str = ""
