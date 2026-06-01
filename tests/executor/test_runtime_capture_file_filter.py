"""Unit tests for the runtime-capture path relevance filter.

W22: with B synthesizing an ``onCommand`` attempt per contributed command, the
harness rewrites ``/workspace/.extrace-harness/context.json`` once per
harness-routed attempt. Those writes are harness bookkeeping, not
target-extension behavior, and previously flooded the file-event capture (and
the language server's ``didChangeWatchedFiles``). The relevance filter — shared
by both the inotify and strace parsers — now drops them.
"""

from __future__ import annotations

from executor.flows.playwright.runtime_capture._shared import (
    _is_harness_artifact_path,
    _is_relevant_file_path,
)


def test_workspace_and_home_paths_are_relevant() -> None:
    assert _is_relevant_file_path("/workspace/src/app.py") is True
    assert _is_relevant_file_path("/home/executor/.ssh/id_rsa") is True


def test_harness_artifact_paths_are_not_relevant() -> None:
    assert _is_relevant_file_path("/workspace/.extrace-harness/context.json") is False
    assert _is_relevant_file_path("/workspace/.extrace-harness/ready.json") is False
    # The directory node itself (e.g. an inotify CREATE,ISDIR event).
    assert _is_relevant_file_path("/workspace/.extrace-harness") is False


def test_noisy_and_empty_paths_are_not_relevant() -> None:
    assert _is_relevant_file_path("") is False
    assert _is_relevant_file_path(".") is False
    assert _is_relevant_file_path("/proc/1/status") is False
    assert _is_relevant_file_path("/home/executor/.vscode/logs/x.log") is False


def test_sibling_directory_is_not_misclassified() -> None:
    # A sibling whose name merely starts with the harness dir name must stay
    # relevant — the filter keys off the exact path component, not a substring.
    assert _is_relevant_file_path("/workspace/.extrace-harness-notes/x.txt") is True
    assert _is_harness_artifact_path("/workspace/.extrace-harness-notes/x.txt") is (
        False
    )
