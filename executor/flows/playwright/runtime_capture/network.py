"""Network capture via tshark."""

from __future__ import annotations

import hashlib
import subprocess
import threading
from collections.abc import Callable
from datetime import datetime
from typing import TypedDict

from packages.analysis_contracts.evidence import redact_secrets

from ._shared import _first_non_empty, _log
from .events import NetworkEvent

_NETWORK_CAPTURE_FILTER = (
    "dns or http.request or http.response or tls.handshake.type == 1 or "
    "(tcp.flags.syn == 1 and tcp.flags.ack == 0)"
)
_HTTP_BODY_PREVIEW_BYTES = 256
_HEX_DIGITS = set("0123456789abcdefABCDEF")
_HEX_SEPARATORS = {":", " ", "\t", "\r", "\n"}


class _BodyMetadata(TypedDict):
    sha256: str
    preview: str
    truncated: bool


def parse_tshark_event_line(
    line: str,
    monitoring_start: float = 0.0,
) -> NetworkEvent | None:
    """Parse a single tshark TSV line into a structured network event."""
    if not line.strip():
        return None

    parts = line.rstrip("\n").split("\t")
    if len(parts) < 17:
        parts.extend([""] * (17 - len(parts)))

    timestamp_raw = parts[0].strip()
    try:
        timestamp_epoch = float(timestamp_raw)
    except ValueError:
        return None

    source_ip = _first_non_empty(parts[1], parts[2])
    destination_ip = _first_non_empty(parts[3], parts[4])
    destination_port_raw = _first_non_empty(parts[5], parts[6])
    dns_query = parts[7].strip()
    http_host = parts[8].strip()
    http_uri = parts[9].strip()
    tls_sni = parts[10].strip()
    protocol = parts[11].strip().lower()
    info = parts[12].strip()
    http_method = parts[13].strip()
    http_status_code_raw = parts[14].strip()
    http_content_type = parts[15].strip()
    http_body_hex = parts[16].strip()

    destination_port = None
    if destination_port_raw:
        try:
            destination_port = int(destination_port_raw)
        except ValueError:
            destination_port = None

    host = _first_non_empty(http_host, tls_sni, dns_query)
    http_status_code = None
    if http_status_code_raw:
        try:
            http_status_code = int(http_status_code_raw)
        except ValueError:
            http_status_code = None

    if http_method:
        event_type = "http_request"
    elif http_status_code is not None:
        event_type = "http_response"
    elif http_host and http_uri:
        event_type = "http_request"
    elif dns_query:
        event_type = "dns_query"
    elif tls_sni:
        event_type = "tls_client_hello"
    else:
        event_type = "tcp_connect"

    timestamp = datetime.fromtimestamp(timestamp_epoch).isoformat(
        timespec="milliseconds"
    )
    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(timestamp_epoch - monitoring_start, 0.0), 3)

    # W14-3 (M13): URI / summary fields carry extension-controlled query
    # strings; bearer tokens, API keys, OAuth params can ride in
    # `?api_key=...` style URLs that previously surfaced verbatim in
    # ActivationReport network events. Route both fields through the same
    # `redact_secrets()` chokepoint that already covers `*_body_preview`
    # (W12-5) and `arguments_preview` (W13-6).
    summary_raw = info or " ".join(
        part for part in [event_type, host or destination_ip, http_uri] if part
    )
    summary = redact_secrets(summary_raw)
    redacted_path = redact_secrets(http_uri)

    if not any([source_ip, destination_ip, host, summary]):
        return None

    request_body = _empty_body_metadata()
    response_body = _empty_body_metadata()
    if event_type == "http_request":
        request_body = _bounded_body_metadata(http_body_hex, http_content_type)
    elif event_type == "http_response":
        response_body = _bounded_body_metadata(http_body_hex, http_content_type)

    return NetworkEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        protocol=protocol or event_type.replace("_", ""),
        event_type=event_type,
        source_ip=source_ip,
        destination_ip=destination_ip,
        destination_port=destination_port,
        host=host,
        path=redacted_path,
        http_method=http_method,
        http_status_code=http_status_code,
        http_content_type=http_content_type,
        request_body_sha256=request_body["sha256"],
        request_body_preview=request_body["preview"],
        request_body_truncated=request_body["truncated"],
        response_body_sha256=response_body["sha256"],
        response_body_preview=response_body["preview"],
        response_body_truncated=response_body["truncated"],
        summary=summary,
    )


def _empty_body_metadata() -> _BodyMetadata:
    return {"sha256": "", "preview": "", "truncated": False}


def _bounded_body_metadata(
    payload_value: str,
    content_type: str,
) -> _BodyMetadata:
    raw_bytes = _decode_body_payload(payload_value)
    if not raw_bytes:
        return _empty_body_metadata()

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if not _is_textual_content_type(content_type):
        return {"sha256": sha256, "preview": "", "truncated": True}

    preview_bytes = raw_bytes[:_HTTP_BODY_PREVIEW_BYTES]
    preview_text = preview_bytes.decode("utf-8", errors="replace")
    return {
        "sha256": sha256,
        "preview": redact_secrets(preview_text),
        "truncated": len(raw_bytes) > _HTTP_BODY_PREVIEW_BYTES,
    }


def _decode_body_payload(payload_value: str) -> bytes:
    stripped = payload_value.strip()
    if not stripped:
        return b""
    if _looks_like_hex_dump(stripped):
        cleaned = "".join(ch for ch in stripped if ch not in _HEX_SEPARATORS)
        try:
            return bytes.fromhex(cleaned)
        except ValueError:
            return b""
    return stripped.encode("utf-8", errors="replace")


def _looks_like_hex_dump(payload_value: str) -> bool:
    if not any(separator in payload_value for separator in _HEX_SEPARATORS):
        return False
    cleaned = "".join(ch for ch in payload_value if ch not in _HEX_SEPARATORS)
    return (
        bool(cleaned)
        and len(cleaned) % 2 == 0
        and all(ch in _HEX_DIGITS for ch in cleaned)
    )


def _is_textual_content_type(content_type: str) -> bool:
    normalized = content_type.lower()
    if not normalized:
        return False
    return normalized.startswith("text/") or any(
        token in normalized
        for token in (
            "json",
            "xml",
            "javascript",
            "x-www-form-urlencoded",
            "graphql",
        )
    )


class NetworkCapture:
    """Capture network events from inside the executor container using tshark."""

    def __init__(
        self,
        monitoring_start: float,
        on_event: Callable[[NetworkEvent], None] | None = None,
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events: list[NetworkEvent] = []
        self.start_error = ""
        self.capture_error = ""
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._stderr_output = ""

    def start(self) -> None:
        """Start background tshark capture."""
        cmd = [
            "tshark",
            "-l",
            "-n",
            "-Q",
            "-i",
            "any",
            "-T",
            "fields",
            "-E",
            "separator=\t",
            "-E",
            "occurrence=f",
            "-e",
            "frame.time_epoch",
            "-e",
            "ip.src",
            "-e",
            "ipv6.src",
            "-e",
            "ip.dst",
            "-e",
            "ipv6.dst",
            "-e",
            "tcp.dstport",
            "-e",
            "udp.dstport",
            "-e",
            "dns.qry.name",
            "-e",
            "http.host",
            "-e",
            "http.request.uri",
            "-e",
            "tls.handshake.extensions_server_name",
            "-e",
            "_ws.col.Protocol",
            "-e",
            "_ws.col.Info",
            "-e",
            "http.request.method",
            "-e",
            "http.response.code",
            "-e",
            "http.content_type",
            "-e",
            "http.file_data",
            "-Y",
            _NETWORK_CAPTURE_FILTER,
        ]
        try:
            self._proc = subprocess.Popen(  # nosec B603,B607
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.start_error = "tshark binary not available in executor container."
            _log(self.start_error)
            return
        except OSError as exc:
            self.start_error = f"tshark start failed: {exc}"
            _log(self.start_error)
            return

        try:
            self._proc.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            pass
        else:
            self._record_capture_error()
            return

        self._reader = threading.Thread(target=self._consume_stdout, daemon=True)
        self._reader.start()
        _log("Network capture started")

    def stop(self) -> list[NetworkEvent]:
        """Stop capture and return all collected events."""
        if self._proc is None:
            return list(self.events)

        was_running = self._proc.poll() is None
        if was_running:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=3)

        if self._reader is not None:
            self._reader.join(timeout=3)

        if not was_running:
            self._record_capture_error()
        else:
            self._drain_stderr()

        _log(f"Network capture stopped with {len(self.events)} event(s)")
        return list(self.events)

    def _consume_stdout(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return

        for line in self._proc.stdout:
            event = parse_tshark_event_line(line, self.monitoring_start)
            if event is None:
                continue
            self.events.append(event)
            if self.on_event is not None:
                self.on_event(event)

    def _record_capture_error(self) -> None:
        if self._proc is None:
            return
        returncode = self._proc.returncode
        if returncode in (None, 0):
            self._drain_stderr()
            return
        stderr_output = self._drain_stderr()
        detail = stderr_output or f"tshark exited with rc={returncode}"
        self.capture_error = f"tshark capture exited unexpectedly: {detail[:240]}"
        self.start_error = self.capture_error
        _log(self.capture_error)

    def _drain_stderr(self) -> str:
        if self._proc is None or self._proc.stderr is None:
            return self._stderr_output
        stderr_output = self._proc.stderr.read().strip()
        if stderr_output:
            collapsed = " ".join(
                line.strip() for line in stderr_output.splitlines() if line.strip()
            )
            if collapsed:
                self._stderr_output = collapsed
        return self._stderr_output
