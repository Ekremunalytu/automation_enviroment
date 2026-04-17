"""Helpers for capture-layer health checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def summarize_extension_host_logs(
    log_offsets: dict[str, int],
    log_paths: list[Path],
) -> dict[str, Any]:
    """Summarize extension-host log availability for the current run."""
    found = bool(log_paths)
    post_start_bytes = 0

    for log_path in log_paths:
        try:
            current_size = log_path.stat().st_size
        except OSError:
            continue
        baseline = max(log_offsets.get(str(log_path.resolve()), 0), 0)
        if current_size > baseline:
            post_start_bytes += current_size - baseline

    return {
        "extension_host_log_found": found,
        "extension_host_log_present": found and post_start_bytes > 0,
        "post_start_bytes": post_start_bytes,
    }
