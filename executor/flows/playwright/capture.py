"""Compatibility wrapper for capture-layer health checks."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from .runtime_capture.log_summary import summarize_extension_host_logs

__all__ = ["summarize_extension_host_logs"]
