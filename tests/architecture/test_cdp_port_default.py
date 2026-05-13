"""W14-3 architecture gate: the CDP remote-debugging port must be
strictly opt-in.

Closes the M14b audit (`[FOLLOWUP
codex-2026-05-10-M14b-cdp-port-default-disabled]`).

Pre-W14-3, the executor container always passed
``--remote-debugging-port=9222`` to VS Code via the
``EXECUTOR_CDP_PORT:-9222`` fallback baked into ``launch_vscode.sh``,
``start.sh``, and ``docker-compose.yml``. A same-container analyzed
extension could reach the unauthenticated CDP socket on ``localhost``
and drive VS Code's chrome instance directly. W14-3 makes CDP opt-in:
the env var defaults to empty across all three sources, and the
launch wrapper appends the ``--remote-debugging-port`` flag only when a
non-empty port is supplied. Operators who need CDP run ``make up-debug``
(which sets ``EXECUTOR_CDP_PORT=9222`` for the ``debug`` profile).

Three content-level invariants are pinned here:

1. ``test_launch_script_defaults_cdp_port_to_empty`` — the
   ``CDP_PORT="${EXECUTOR_CDP_PORT:-}"`` shape must NOT fall back to
   ``9222`` in ``launch_vscode.sh``.

2. ``test_launch_script_appends_cdp_flag_conditionally`` — the
   ``code`` invocation must NOT carry an unconditional
   ``--remote-debugging-port=`` argument; the flag must live behind a
   non-empty CDP_PORT check.

3. ``test_start_script_defaults_cdp_port_to_empty`` — ``start.sh``
   mirrors the same empty default so the env passthrough into
   ``launch_vscode.sh`` carries the opt-in semantics through.

4. ``test_docker_compose_defaults_cdp_port_to_empty`` —
   ``docker-compose.yml`` must source ``EXECUTOR_CDP_PORT`` with an
   empty default (the host-side ``executor-cdp`` sidecar under the
   ``debug`` profile keeps its own 9222 fallback because the
   ``up-debug`` Makefile lane explicitly sets the variable before
   invoking compose).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCH_SCRIPT = REPO_ROOT / "executor" / "container" / "launch_vscode.sh"
START_SCRIPT = REPO_ROOT / "executor" / "container" / "start.sh"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def test_launch_script_defaults_cdp_port_to_empty() -> None:
    """`launch_vscode.sh` must source EXECUTOR_CDP_PORT without a default."""
    content = LAUNCH_SCRIPT.read_text(encoding="utf-8")
    assert 'CDP_PORT="${EXECUTOR_CDP_PORT:-}"' in content, (
        f"{LAUNCH_SCRIPT.relative_to(REPO_ROOT)} must default CDP_PORT to "
        "the empty string so a missing EXECUTOR_CDP_PORT keeps the "
        "remote-debugging flag off."
    )
    # Explicit negative: the legacy 9222 default must NOT appear in the
    # CDP_PORT line.
    assert 'CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"' not in content, (
        f"{LAUNCH_SCRIPT.relative_to(REPO_ROOT)} re-introduced the default "
        "9222 CDP fallback; CDP must stay opt-in per W14-3 M14b."
    )


def test_launch_script_appends_cdp_flag_conditionally() -> None:
    """The CDP flag must live behind a non-empty CDP_PORT guard."""
    content = LAUNCH_SCRIPT.read_text(encoding="utf-8")
    # Unconditional shape (pre-W14-3) MUST be absent — the literal flag
    # cannot sit on its own line as a positional `code` argument.
    assert '--remote-debugging-port="${CDP_PORT}" \\' not in content, (
        f"{LAUNCH_SCRIPT.relative_to(REPO_ROOT)} re-introduced the "
        "unconditional --remote-debugging-port argument; the flag must "
        "be conditionally appended through the CDP_FLAG array."
    )
    # Conditional shape MUST be present.
    assert 'if [ -n "${CDP_PORT}" ]; then' in content, (
        f"{LAUNCH_SCRIPT.relative_to(REPO_ROOT)} must guard the CDP "
        "flag behind a non-empty CDP_PORT check."
    )
    assert "CDP_FLAG=(--remote-debugging-port=" in content, (
        f"{LAUNCH_SCRIPT.relative_to(REPO_ROOT)} must populate the "
        "CDP_FLAG array with the --remote-debugging-port argument inside "
        "the non-empty-CDP_PORT branch."
    )


def test_start_script_defaults_cdp_port_to_empty() -> None:
    """`start.sh` must mirror the empty default so env passthrough stays opt-in."""
    content = START_SCRIPT.read_text(encoding="utf-8")
    assert 'CDP_PORT="${EXECUTOR_CDP_PORT:-}"' in content, (
        f"{START_SCRIPT.relative_to(REPO_ROOT)} must default CDP_PORT to "
        "the empty string so the env passthrough into launch_vscode.sh "
        "carries the opt-in semantics."
    )
    assert 'CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"' not in content, (
        f"{START_SCRIPT.relative_to(REPO_ROOT)} re-introduced the default "
        "9222 CDP fallback; CDP must stay opt-in per W14-3 M14b."
    )


def test_docker_compose_defaults_cdp_port_to_empty() -> None:
    """`docker-compose.yml` must source EXECUTOR_CDP_PORT with empty default
    for the executor service. The host-side `executor-cdp` sidecar keeps
    its own 9222 fallback because the `make up-debug` lane explicitly
    sets the env var before invoking compose.
    """
    content = COMPOSE_FILE.read_text(encoding="utf-8")
    # Executor service env line must use the empty default.
    assert "EXECUTOR_CDP_PORT: ${EXECUTOR_CDP_PORT:-}" in content, (
        f"{COMPOSE_FILE.relative_to(REPO_ROOT)} must source "
        "EXECUTOR_CDP_PORT with an empty default for the executor "
        "service so an unset env var keeps CDP off."
    )
