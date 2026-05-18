"""W13-1 / W13-11 security primitives for harness handshake authentication.

Lifted out of ``reconciliation.py`` at W16-4 to give the HMAC marker
verification and the per-launch secret eager-consume their own narrow
module. The primitives here own:

* ``HARNESS_PYTHON_SECRET_PATH`` (W13-1 file-fallback location).
* ``load_harness_python_secret`` (W13-11 env-priority load + defense-
  in-depth unlink — fail-closed when neither env nor file provides a
  value).
* ``_verify_harness_marker_signature`` (W13-1 HMAC-SHA256 verification
  over canonical-JSON, constant-time compare).

Behavior is byte-identical with the pre-W16-4 inline implementations.
The architecture gates at
``tests/architecture/test_harness_secret_eager_consume.py`` and
``tests/architecture/test_harness_marker_auth.py`` were re-targeted at
this file's path so the structural invariants survive the rename. The
behavioral suite at
``tests/executor/test_playwright_health_reconciliation.py`` exercises
the load helper directly; tests now import from this module by name.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

# W13-1 (Codex H6): file path the harness orchestration writes the per-
# launch HMAC secret to. ``launch_vscode.sh`` produces this file before
# every VS Code start (boot and reset); ``load_harness_python_secret``
# reads it once and unlinks so the same-UID target extension cannot
# reach the value via the bind-mounted ``/results`` directory after the
# Python orchestration has consumed it.
HARNESS_PYTHON_SECRET_PATH = Path(
    os.environ.get(
        "EXECUTOR_HARNESS_PYTHON_SECRET_PATH",
        "/results/_extrace_harness_python_secret",
    )
)


def load_harness_python_secret(
    path: Path = HARNESS_PYTHON_SECRET_PATH,
) -> str:
    """Read the per-launch harness HMAC secret then unlink the file.

    W13-11 (Codex F1 close-pass for W13-1 H6): production paths receive
    the secret via the ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` env var
    populated on the host by
    ``executor.host.consume_harness_python_secret_eager`` BEFORE the
    analyzed VSIX is admitted to the executor sandbox. The env var is
    read first; the legacy file fallback is preserved for unit-test
    paths that construct ``ActivationReport`` directly without going
    through host-side eager-consume.

    Returns the stripped secret string, or empty string if neither
    source provides one. Always attempts the unlink (even on env hit)
    so a stale file from a crashed eager-consume cannot persist into
    the next launch cycle.
    """
    env_value = os.environ.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", "").strip()
    if env_value:
        # Defense-in-depth: even when env wins, attempt to unlink the
        # legacy file in case ``launch_vscode.sh`` ran but eager-consume
        # crashed before reaping it — keeps the target-readable window
        # from persisting across reset cycles.
        with contextlib.suppress(FileNotFoundError, OSError):
            path.unlink()
        return env_value
    # Legacy path — preserved verbatim for test compatibility.
    secret = ""
    try:
        secret = path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        secret = ""
    with contextlib.suppress(FileNotFoundError, OSError):
        path.unlink()
    return secret


def _verify_harness_marker_signature(
    payload: dict[str, Any],
    expected_nonce: str,
) -> bool:
    """W13-1 (Codex H6): authenticate a ``[extrace-harness]`` marker payload.

    Computes HMAC-SHA256 over ``canonical_json(payload \\ {"nonce"})`` using
    ``expected_nonce`` (loaded from ``/results/_extrace_harness_python_secret``
    by the entrypoint) and compares against ``payload["nonce"]`` in constant
    time. The canonical form is sorted-keys JSON without whitespace, in
    lockstep with ``markers.js::_canonicalPayloadBytes`` and the
    ``_w13_1_canonical_payload`` test helper. Same-UID target extensions
    cannot reach the secret, so a forged marker without a matching
    signature is rejected.

    Fail-closed semantics: empty ``expected_nonce``, missing/non-string
    ``nonce`` in payload, or invalid signature all return False. The
    empty-nonce branch preserves the pre-W13-1 unit-test contract where
    ``ActivationReport`` is constructed without the orchestration
    handshake; production paths run with a populated secret and reject
    unsigned markers.
    """
    if not expected_nonce:
        return False
    received = payload.get("nonce")
    if not isinstance(received, str) or not received:
        return False
    canonical = json.dumps(
        {k: v for k, v in payload.items() if k != "nonce"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_sig = hmac.new(
        expected_nonce.encode("utf-8"),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received, expected_sig)


__all__ = [
    "HARNESS_PYTHON_SECRET_PATH",
    "_verify_harness_marker_signature",
    "load_harness_python_secret",
]
