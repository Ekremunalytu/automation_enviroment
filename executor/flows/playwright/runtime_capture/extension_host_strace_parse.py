"""Extension Host strace process-event parsing (W12-5 split from extension_host.py)."""

from __future__ import annotations

import re
from datetime import datetime

from packages.analysis_contracts.evidence import redact_secrets

from .events import ProcessEvent

_PROCESS_EVENT_RE = re.compile(
    r"^(?:\[pid\s+(?P<pid>\d+)\]\s+)?(?P<ts>\d+\.\d+)\s+"
    r"(?P<call>execve|execveat|clone|clone3|fork|vfork|chdir)\((?P<args>.*)\)\s+=\s+(?P<result>.+)$"
)
_PROCESS_ARGUMENT_PREVIEW = 256


def parse_strace_process_event_line(
    line: str,
    *,
    monitoring_start: float = 0.0,
    root_pid: int,
    ppid_by_pid: dict[int, int | None],
    cwd_by_pid: dict[int, str],
) -> ProcessEvent | None:
    match = _PROCESS_EVENT_RE.match(line.strip())
    if match is None:
        return None

    try:
        timestamp_epoch = float(match.group("ts"))
    except ValueError:
        return None

    call = match.group("call")
    args = match.group("args")
    result = match.group("result").strip()
    current_pid = int(match.group("pid") or root_pid)
    current_ppid = ppid_by_pid.get(current_pid)
    current_cwd = cwd_by_pid.get(current_pid, "")
    rel_time_s = None
    if monitoring_start > 0:
        rel_time_s = round(max(timestamp_epoch - monitoring_start, 0.0), 3)
    timestamp = datetime.fromtimestamp(timestamp_epoch).isoformat(
        timespec="milliseconds"
    )

    if call in {"clone", "clone3", "fork", "vfork"}:
        try:
            child_pid = int(result.split()[0])
        except ValueError:
            return None
        ppid_by_pid[child_pid] = current_pid
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=child_pid,
            ppid=current_pid,
            operation="spawn",
            command=redact_secrets(call),
            arguments_preview=_bounded_arguments_preview(args),
            cwd=redact_secrets(current_cwd),
            summary=redact_secrets(
                f"Spawned child process {child_pid} from pid {current_pid}."
            ),
        )

    quoted_items = re.findall(r'"([^"]*)"', args)
    if call in {"execve", "execveat"}:
        if not quoted_items:
            return None
        command = redact_secrets(quoted_items[0])
        arguments_preview = _bounded_arguments_preview(" ".join(quoted_items[1:]))
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=current_pid,
            ppid=current_ppid,
            operation="exec",
            command=command,
            arguments_preview=arguments_preview,
            cwd=redact_secrets(current_cwd),
            summary=redact_secrets(f"Executed {command} in pid {current_pid}."),
        )

    if call == "chdir":
        if not quoted_items:
            return None
        cwd_by_pid[current_pid] = quoted_items[0]
        return ProcessEvent(
            timestamp=timestamp,
            rel_time_s=rel_time_s,
            pid=current_pid,
            ppid=current_ppid,
            operation="chdir",
            command=redact_secrets("chdir"),
            arguments_preview="",
            cwd=redact_secrets(quoted_items[0]),
            summary=redact_secrets(f"Changed working directory to {quoted_items[0]}."),
        )

    return None


def _bounded_arguments_preview(raw: str) -> str:
    # W13-6: redact secrets before truncation so the cap can never cut through
    # a placeholder, and so the three call sites (clone/exec/chdir) inherit
    # redaction at this single chokepoint.
    redacted = redact_secrets(raw)
    preview = " ".join(redacted.split())
    if len(preview) <= _PROCESS_ARGUMENT_PREVIEW:
        return preview
    return preview[: _PROCESS_ARGUMENT_PREVIEW - 3] + "..."
