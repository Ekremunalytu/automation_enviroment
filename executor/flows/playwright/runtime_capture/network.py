"""Network capture via tshark."""

from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from datetime import datetime

from ._shared import _first_non_empty, _log
from .events import NetworkEvent

_NETWORK_CAPTURE_FILTER = (
    "dns or http.request or tls.handshake.type == 1 or "
    "(tcp.flags.syn == 1 and tcp.flags.ack == 0)"
)


def parse_tshark_event_line(
    line: str,
    monitoring_start: float = 0.0,
) -> NetworkEvent | None:
    """Parse a single tshark TSV line into a structured network event."""
    if not line.strip():
        return None

    parts = line.rstrip("\n").split("\t")
    if len(parts) < 13:
        parts.extend([""] * (13 - len(parts)))

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

    destination_port = None
    if destination_port_raw:
        try:
            destination_port = int(destination_port_raw)
        except ValueError:
            destination_port = None

    host = _first_non_empty(http_host, tls_sni, dns_query)
    if http_host and http_uri:
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

    summary = info or " ".join(
        part for part in [event_type, host or destination_ip, http_uri] if part
    )

    if not any([source_ip, destination_ip, host, summary]):
        return None

    return NetworkEvent(
        timestamp=timestamp,
        rel_time_s=rel_time_s,
        protocol=protocol or event_type.replace("_", ""),
        event_type=event_type,
        source_ip=source_ip,
        destination_ip=destination_ip,
        destination_port=destination_port,
        host=host,
        path=http_uri,
        summary=summary,
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
        self._proc: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None

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
            "-Y",
            _NETWORK_CAPTURE_FILTER,
        ]
        try:
            self._proc = subprocess.Popen(  # nosec B603,B607
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
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

        self._reader = threading.Thread(target=self._consume_stdout, daemon=True)
        self._reader.start()
        _log("Network capture started")

    def stop(self) -> list[NetworkEvent]:
        """Stop capture and return all collected events."""
        if self._proc is None:
            return list(self.events)

        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=3)

        if self._reader is not None:
            self._reader.join(timeout=3)

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
