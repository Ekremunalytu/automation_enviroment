"""Extension Host log discovery, activation parsing, and strace capture.

W12-5 thin re-export facade. Production code should import from the focused
modules directly:

- ``extension_host_log_parse`` — activation log parsing + file discovery.
- ``extension_host_strace_parse`` — strace process-event parsing.
- ``extension_host_capture`` — ``ExtensionHostFileCapture`` + watch/poll loops.

This facade survives so existing callers keep working without a flag day:

- ``executor/flows/playwright/monitor/__init__.py`` re-exports 7 of these
  names from this module path.
- ``executor/flows/playwright/monitor/sources.py`` imports
  ``_activation_within_monitoring_window`` and ``_parse_activation_lines``
  from this module path.
- ``tests/executor/test_playwright_extension_host.py`` (23 cases) accesses
  9 distinct symbols via attribute lookup on the imported module.
"""

from ._shared import VSCODE_LOGS_DIR as VSCODE_LOGS_DIR
from ._shared import _parse_iso_timestamp as _parse_iso_timestamp
from .extension_host_capture import (
    ExtensionHostFileCapture as ExtensionHostFileCapture,
)
from .extension_host_capture import (
    _poll_exthost_log as _poll_exthost_log,
)
from .extension_host_capture import (
    watch_exthost_log as watch_exthost_log,
)
from .extension_host_log_parse import (
    _ACTIVATION_PATTERNS as _ACTIVATION_PATTERNS,
)
from .extension_host_log_parse import (
    _LIFECYCLE_MARKER_PATTERNS as _LIFECYCLE_MARKER_PATTERNS,
)
from .extension_host_log_parse import (
    _TIMESTAMP_RE as _TIMESTAMP_RE,
)
from .extension_host_log_parse import (
    _activation_within_monitoring_window as _activation_within_monitoring_window,
)
from .extension_host_log_parse import (
    _parse_activation_lines as _parse_activation_lines,
)
from .extension_host_log_parse import (
    find_exthost_logs as find_exthost_logs,
)
from .extension_host_log_parse import (
    parse_activations_from_log as parse_activations_from_log,
)
from .extension_host_log_parse import (
    parse_activations_from_output as parse_activations_from_output,
)
from .extension_host_log_parse import (
    parse_all_exthost_logs as parse_all_exthost_logs,
)
from .extension_host_log_parse import (
    read_extension_host_output as read_extension_host_output,
)
from .extension_host_strace_parse import (
    _PROCESS_EVENT_RE as _PROCESS_EVENT_RE,
)
from .extension_host_strace_parse import (
    parse_strace_process_event_line as parse_strace_process_event_line,
)

__all__ = [
    "VSCODE_LOGS_DIR",
    "_ACTIVATION_PATTERNS",
    "_LIFECYCLE_MARKER_PATTERNS",
    "_PROCESS_EVENT_RE",
    "_TIMESTAMP_RE",
    "ExtensionHostFileCapture",
    "_activation_within_monitoring_window",
    "_parse_activation_lines",
    "_parse_iso_timestamp",
    "_poll_exthost_log",
    "find_exthost_logs",
    "parse_activations_from_log",
    "parse_activations_from_output",
    "parse_all_exthost_logs",
    "parse_strace_process_event_line",
    "read_extension_host_output",
    "watch_exthost_log",
]
