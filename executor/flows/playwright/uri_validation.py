"""URI validation + argv-form launcher for trigger stimulus (W8-3).

Restricts external URI handling to a small allow-list of schemes and
invokes ``xdg-open`` directly through ``subprocess.run`` in argv form so
that adversarial URI payloads cannot reach a shell interpreter.

Replaces the legacy ``terminal.type_in_terminal(page, f"xdg-open '{uri}'")``
sites in ``entrypoint_triggers.py`` and ``stimulus_attempts.py`` (see
``documents/active-work/W8-security.md`` item W8-3).
"""

from __future__ import annotations

import subprocess
from urllib.parse import urlparse

ALLOWED_URI_SCHEMES: frozenset[str] = frozenset(
    {"vscode", "vscode-insiders", "http", "https"}
)

# Inline constant: this module is also imported directly as ``uri_validation``
# by the executor compatibility tests, so keep the runtime helper independent
# from the host-side ``executor.binary_paths`` module. That module mirrors this
# value, and ``tests/executor/test_absolute_paths.py`` checks the two stay in
# sync.
XDG_OPEN_PATH = "/usr/bin/xdg-open"

DEFAULT_TIMEOUT_S = 5.0

__all__ = [
    "ALLOWED_URI_SCHEMES",
    "DEFAULT_TIMEOUT_S",
    "XDG_OPEN_PATH",
    "UriValidationError",
    "run_uri_trigger",
    "validate_uri_scheme",
]


class UriValidationError(ValueError):
    """Raised when a trigger URI fails scheme allow-list validation."""


def validate_uri_scheme(uri: str) -> str:
    """Return ``uri`` unchanged when its scheme is allow-listed, else raise.

    Empty schemes, opaque/relative URIs, and any non-allow-listed scheme
    raise :class:`UriValidationError`. The allow-list is intentionally
    narrow: ``vscode``, ``vscode-insiders``, ``http``, ``https`` cover
    every legitimate trigger payload produced by
    ``packages/analysis_planner/selection.py`` while rejecting
    ``file:``, ``javascript:``, ``data:``, and shell-injection probes.
    """
    if not isinstance(uri, str) or not uri:
        raise UriValidationError(f"URI trigger must be a non-empty string: {uri!r}")
    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()
    if not scheme:
        raise UriValidationError(f"URI trigger missing scheme: {uri!r}")
    if scheme not in ALLOWED_URI_SCHEMES:
        raise UriValidationError(
            f"URI scheme not allowed for trigger: {scheme!r} (allowed: "
            f"{sorted(ALLOWED_URI_SCHEMES)})"
        )
    return uri


def run_uri_trigger(
    uri: str, *, timeout_s: float = DEFAULT_TIMEOUT_S
) -> subprocess.CompletedProcess[str]:
    """Validate ``uri`` then invoke ``/usr/bin/xdg-open`` in argv form.

    The subprocess call is argv-list (no ``shell=True``) and uses an
    absolute binary path so that container ``$PATH`` cannot be used to
    swap the launcher. ``check=False`` is intentional — caller decides
    whether a non-zero exit blocks the surrounding trigger flow.
    """
    validated = validate_uri_scheme(uri)
    return subprocess.run(
        [XDG_OPEN_PATH, validated],
        check=False,
        timeout=timeout_s,
        capture_output=True,
        text=True,
    )
