"""W10-5 contract tests: validate_executor_action narrows the
planner→dispatcher action surface.

Closes [FOLLOWUP planner-executor-action-enum]. Pre-W10-5 the planner
emitted raw strings and the playwright dispatcher matched them with raw
``startswith``/``==`` branches; a typo in either layer became a
runtime "Unsupported stimulus action" error long after the planner
phase. The validator pins the namespace + extra-action sets so mistakes
fail fast at producer time.
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts import (
    EXECUTOR_ACTION_NAMESPACES,
    EXTRA_EXECUTOR_ACTIONS,
    validate_executor_action,
)


_EXPECTED_NAMESPACES = frozenset(
    {
        "scenario:",
        "command:",
        "extra:",
        "fixture:",
        "harness:",
    }
)

_EXPECTED_EXTRA_ACTIONS = frozenset(
    {
        "extra:task_trigger",
        "extra:debug_lifecycle",
        "extra:walkthrough",
        "extra:uri_trigger",
        "extra:custom_editor",
    }
)


def test_namespace_set_matches_dispatcher_branches() -> None:
    assert EXECUTOR_ACTION_NAMESPACES == _EXPECTED_NAMESPACES


def test_extra_action_set_matches_dispatcher_branches() -> None:
    assert EXTRA_EXECUTOR_ACTIONS == _EXPECTED_EXTRA_ACTIONS


@pytest.mark.parametrize("action", sorted(_EXPECTED_EXTRA_ACTIONS))
def test_validate_accepts_each_known_extra_action(action: str) -> None:
    assert validate_executor_action(action) == action


@pytest.mark.parametrize(
    "action",
    [
        "scenario:coding_session",
        "scenario:project_exploration",
        "command:auto",
        "command:Tasks: Run Task",
        "fixture:startup_observe",
        "harness:run_current_stimulus",
    ],
)
def test_validate_accepts_namespace_prefixed_actions(action: str) -> None:
    assert validate_executor_action(action) == action


def test_validate_passes_empty_string_through() -> None:
    """Empty action is the planner's sentinel for "no backfill"; it
    must not trip the validator."""
    assert validate_executor_action("") == ""


def test_validate_rejects_unknown_extra_action() -> None:
    """Catches typos in the extra: closed set."""
    with pytest.raises(ValueError, match="Unknown extra:"):
        validate_executor_action("extra:typo_action")


def test_validate_rejects_unknown_namespace() -> None:
    """Catches an entirely unknown namespace prefix."""
    with pytest.raises(ValueError, match="does not match any known namespace"):
        validate_executor_action("invented:foo")


def test_validate_rejects_namespace_with_empty_tail() -> None:
    """``scenario:`` with no scenario name is meaningless dispatch
    input; must fail at producer time, not silently dispatch."""
    with pytest.raises(ValueError, match="empty tail"):
        validate_executor_action("scenario:")


def test_validate_rejects_bare_namespace_word_without_colon() -> None:
    with pytest.raises(ValueError, match="does not match any known namespace"):
        validate_executor_action("scenario")
