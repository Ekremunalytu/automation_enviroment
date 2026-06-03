"""Inter-command maintenance for the layered stimulus loop (W22 Fix 4b/4c).

Distinct from ``attempts.py`` (which knows how to *execute* one attempt): this
module owns what happens *between* command attempts — reclaiming leftover
terminals and gating on renderer liveness — so the many synthesized
contributes-command attempts do not accumulate load or hammer a renderer that
has already died.
"""

from __future__ import annotations

import contextlib
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .. import automation
from ..vscode import commands, terminal

_COMMAND_ACTION_PREFIXES: tuple[str, ...] = ("command:", "harness:")

# Substrings that mark a synthesized contributes-command as terminal/REPL
# spawning. Such commands leave a live terminal plus child processes behind;
# killing them between attempts (Fix 4c) stops the pile-up that, combined with
# the file storm, exhausted the renderer in the field (createTerminal,
# execInTerminal*, startREPL, startNativeREPL, execInREPL, …).
_TERMINAL_COMMAND_HINTS: tuple[str, ...] = ("terminal", "repl")


def _is_command_action(action: str) -> bool:
    return action.startswith(_COMMAND_ACTION_PREFIXES)


def _is_terminal_command_attempt(attempt: dict[str, Any], action: str) -> bool:
    if not _is_command_action(action):
        return False
    haystack = " ".join(
        (
            str(attempt.get("event_value", "")),
            str(attempt.get("activation_event", "")),
        )
    ).lower()
    return any(hint in haystack for hint in _TERMINAL_COMMAND_HINTS)


def post_command_maintenance(
    page: Page,
    attempt: dict[str, Any],
    action: str,
    *,
    monitor: Any | None = None,
) -> bool:
    """Inter-command cleanup + renderer health gate (W22 Fix 4b/4c).

    Runs after a command attempt finishes. For a terminal/REPL-spawning command
    it kills the leftover terminals (4c) so they do not accumulate across the
    many synthesized contributes-command attempts. Then it probes renderer
    liveness (4b): a cumulative-load death that happened *between* attempts is
    detected here and reported so the layered loop can abort the remainder
    gracefully, instead of surfacing later as a misleading ``fatal_ui_crash``
    on the next (innocent) attempt. Returns ``True`` when the renderer is dead.
    A no-op (returns ``False``) for non-command actions.
    """
    if not _is_command_action(action):
        return False
    if _is_terminal_command_attempt(attempt, action):
        # Cleanup is best-effort: if the renderer is already dying the kill
        # command may raise — the liveness probe below is the source of truth.
        with contextlib.suppress(
            PlaywrightError, commands.CommandPaletteUnavailableError
        ):
            terminal.close_all_terminals(page)
    return not automation.is_renderer_alive(page)
