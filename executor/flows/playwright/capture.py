"""Compatibility wrapper for capture-layer health checks."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

try:
    from .runtime_capture.log_summary import summarize_extension_host_logs
except ImportError:  # pragma: no cover - top-level executor import mode
    from runtime_capture.log_summary import summarize_extension_host_logs

__all__ = ["summarize_extension_host_logs"]
