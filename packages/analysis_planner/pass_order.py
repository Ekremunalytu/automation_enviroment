"""Stimulus pass ordering and per-run limit constants.

W10-3 split from former monolithic ``registry.py``. Pure data; no behavior.
"""

from __future__ import annotations

_PASS_ORDER = [
    "workspace_bootstrap",
    "ui_first_user_session",
    "target_specific_activation",
    "unresolved_event_backfill",
    "post_run_verification",
]

_PASS_LABELS = {
    "workspace_bootstrap": "workspace/bootstrap pass",
    "ui_first_user_session": "UI-first user session pass",
    "target_specific_activation": "target-specific activation pass",
    "unresolved_event_backfill": "unresolved-event backfill pass",
    "post_run_verification": "post-run verification pass",
}

_PASS_DESCRIPTIONS = {
    "workspace_bootstrap": (
        "Materialize workspace fixtures, launch prerequisites, and startup-aligned "
        "stimuli before visible interaction begins."
    ),
    "ui_first_user_session": (
        "Drive visible VS Code workflows first so user-led evidence stays primary."
    ),
    "target_specific_activation": (
        "Run event-family-specific flows for the target extension's declared "
        "activation surface."
    ),
    "unresolved_event_backfill": (
        "Retry events through deterministic harness paths when the visible UI "
        "cannot reach them reliably."
    ),
    "post_run_verification": (
        "Reconcile activation evidence, target ownership, and per-event outcome "
        "status after execution finishes."
    ),
}

_MAX_SCENARIOS_PER_RUN = 5
_MAX_EXTRA_COMMANDS = 6
