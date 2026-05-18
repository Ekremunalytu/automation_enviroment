"""W13-12 harness handshake helpers — fail-closed dispatch for completion traces.

Lifted out of ``reconciliation.py`` at W16-4 alongside the W13-1
security primitives in ``security.py``. The handshake module owns:

* ``_harness_trace_records_by_attempt`` — extract every
  ``[extrace-harness]`` JSON marker emitted into the extension-host
  output stream and group the payloads by ``attempt_id``.
* ``_attempt_has_harness_completion_trace`` — three-branch dispatch
  that decides whether an attempt has a ``phase=="complete"`` trace
  the production code is willing to count:
    1. ``expected_nonce`` non-empty → require a valid HMAC signature
       (W13-1 contract).
    2. ``expected_nonce`` empty AND ``handshake_required=True`` →
       fail-closed (W13-12). Eager-consume miss / OSError / race —
       target extensions can forge ``phase=="complete"`` lines, so we
       refuse to fall back to phase-only.
    3. ``expected_nonce`` empty AND ``handshake_required=False`` →
       legacy phase-only check (test fixtures that construct
       ``ActivationReport`` without the orchestration handshake).

Behavior is byte-identical with the pre-W16-4 inline implementation.
The architecture gates at
``tests/architecture/test_harness_marker_auth.py`` were re-targeted at
this file's path so the structural invariants survive the rename.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import json
import re
from typing import Any

from .security import _verify_harness_marker_signature

_HARNESS_MARKER_RE = re.compile(r"\[extrace-harness\]\s+(?P<payload>\{.*\})")


def _harness_trace_records_by_attempt(report: Any) -> dict[str, list[dict[str, Any]]]:
    raw_output = str(getattr(report, "extension_host_output", "") or "")
    traces: dict[str, list[dict[str, Any]]] = {}
    for line in raw_output.splitlines():
        marker_match = _HARNESS_MARKER_RE.search(line)
        if marker_match is None:
            continue
        try:
            payload = json.loads(marker_match.group("payload"))
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        attempt_id = str(payload.get("attempt_id", "")).strip()
        if attempt_id:
            traces.setdefault(attempt_id, []).append(payload)
    return traces


def _attempt_has_harness_completion_trace(
    attempt: Any,
    traces_by_attempt: dict[str, list[dict[str, Any]]],
    expected_nonce: str = "",
    *,
    handshake_required: bool = False,
) -> bool:
    """W13-1 / W13-12: a ``phase=="complete"`` trace counts only when its
    HMAC nonce verifies under ``expected_nonce``. Empty ``expected_nonce``
    means the report was built without an orchestration handshake.

    Three branches:

    1. ``expected_nonce`` non-empty → require valid HMAC signature on the
       ``phase=="complete"`` trace (W13-1 contract).
    2. ``expected_nonce`` empty AND ``handshake_required=True`` → fail-
       closed (W13-12). Production paths set ``handshake_required`` via
       ``ActivationReport.harness_handshake_required`` at ``setup_monitor``
       time. An empty ``expected_nonce`` here means the eager-consume
       (W13-11) miss-fired (``FileNotFoundError``, ``OSError``, bind-mount
       race); we refuse to fall back to phase-only because a target
       extension can forge ``[extrace-harness] {phase:"complete"}``.
    3. ``expected_nonce`` empty AND ``handshake_required=False`` → legacy
       phase-only check (test path). Unit fixtures construct
       ``ActivationReport`` directly without the orchestration handshake;
       keeping the phase-only branch preserves the pre-W13-1 contract for
       those fixtures.
    """
    attempt_id = str(getattr(attempt, "attempt_id", "")).strip()
    if not attempt_id:
        return False
    if expected_nonce:
        return any(
            str(trace.get("phase", "")).strip() == "complete"
            and _verify_harness_marker_signature(trace, expected_nonce)
            for trace in traces_by_attempt.get(attempt_id, [])
        )
    if handshake_required:
        # W13-12: production handshake required but secret unavailable →
        # fail-closed. Eager-consume (W13-11) guarantees presence on the
        # happy path; this branch covers the residual failure modes.
        return False
    return any(
        str(trace.get("phase", "")).strip() == "complete"
        for trace in traces_by_attempt.get(attempt_id, [])
    )


__all__ = [
    "_attempt_has_harness_completion_trace",
    "_harness_trace_records_by_attempt",
]
