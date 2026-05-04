"""Typed contract for planner-emitted executor action names (W10-5).

The planner (``packages/analysis_planner/attempts.py::_resolve_executor_action``)
emits short string commands that the playwright dispatcher
(``executor/flows/playwright/stimulus_attempts.py::_dispatch_action``)
matches against to drive the target extension. Pre-W10-5 these were raw
strings on both ends; a typo in either layer became a runtime
"Unsupported stimulus action" error long after the planner phase.

This module pins:

- ``EXECUTOR_ACTION_NAMESPACES`` — the closed set of namespace prefixes
  the dispatcher recognises (``scenario:`` / ``command:`` / ``extra:`` /
  ``fixture:`` / ``harness:``).
- ``EXTRA_EXECUTOR_ACTIONS`` — the 5 fixed action names that live in the
  ``extra:`` namespace and have no parametric tail.
- ``validate_executor_action(...)`` — a fast pre-emit / pre-dispatch
  guard that raises ``ValueError`` if an action does not match either
  the ``extra:`` exact-match set or one of the namespace prefixes.

Keep dispatch explicit. No generic event framework — adding a new
action means amending one of the two sets above and adding a matching
branch in the dispatcher.
"""

from __future__ import annotations

# Exact-match action names within the ``extra:`` namespace. Each one
# corresponds to a non-parametric branch in the playwright dispatcher.
EXTRA_EXECUTOR_ACTIONS: frozenset[str] = frozenset(
    {
        "extra:task_trigger",
        "extra:debug_lifecycle",
        "extra:walkthrough",
        "extra:uri_trigger",
        "extra:custom_editor",
    }
)

# Closed set of action-namespace prefixes the dispatcher recognises.
# ``scenario:``, ``command:``, ``fixture:``, ``harness:`` carry a
# parametric tail (e.g. ``scenario:coding_session``); ``extra:`` is
# closed-set per EXTRA_EXECUTOR_ACTIONS. ``command:auto`` is a special
# command-namespace member but still fits the ``command:`` prefix gate.
EXECUTOR_ACTION_NAMESPACES: frozenset[str] = frozenset(
    {
        "scenario:",
        "command:",
        "extra:",
        "fixture:",
        "harness:",
    }
)


def validate_executor_action(action: str) -> str:
    """Return ``action`` if it matches the typed contract, raise otherwise.

    Empty string is a sentinel for "no action" (e.g. backfill with no
    harness fallback declared) and is allowed through unchanged.
    """
    if action == "":
        return action
    if action.startswith("extra:"):
        if action not in EXTRA_EXECUTOR_ACTIONS:
            raise ValueError(
                f"Unknown extra: executor action {action!r}; expected one of "
                f"{sorted(EXTRA_EXECUTOR_ACTIONS)}"
            )
        return action
    for namespace in EXECUTOR_ACTION_NAMESPACES:
        if action.startswith(namespace):
            tail = action[len(namespace) :]
            if not tail:
                raise ValueError(
                    f"Executor action {action!r} has empty tail after "
                    f"namespace {namespace!r}"
                )
            return action
    raise ValueError(
        f"Executor action {action!r} does not match any known namespace "
        f"in {sorted(EXECUTOR_ACTION_NAMESPACES)}"
    )
