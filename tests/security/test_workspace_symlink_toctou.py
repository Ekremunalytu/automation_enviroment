"""W15-2 behavioral regression: ``clean_workspace()`` must not follow
adversarial symlinks. Codex 2026-05-10 M12 close-out.

Pre-W15-2 ``clean_workspace()`` branched on ``is_dir()`` (which follows
symlinks) before falling through to ``shutil.rmtree``; a symlink-to-
directory inside the workspace therefore (a) caused ``shutil.rmtree``
to raise ``OSError`` (Python ≥3.7 refuses to rmtree a symlink),
leaving the workspace partially cleaned, and (b) opened the broader
concern that the symlink target — operator-controlled state outside
the workspace — must never be touched by automation cleanup.

Post-W15-2 ``clean_workspace()`` checks ``is_symlink()`` first
(mirroring ``reset_state.py:_clear_directory``); the symlink itself is
unlinked and the target is left untouched.

Architecture discipline is pinned by
``tests/architecture/test_workspace_symlink_check_order.py``; this
behavioral suite proves the observable runtime contract on adversarial
fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from executor.flows.playwright import workspace


@pytest.fixture
def isolated_workspace(monkeypatch, tmp_path: Path) -> Path:
    """Create an isolated workspace dir + point ``workspace.WORKSPACE_DIR``
    at it. ``clean_workspace()`` reads ``WORKSPACE_DIR`` at call time
    so the monkeypatch takes effect for the test scope.
    """
    ws = tmp_path / "workspace"
    ws.mkdir()
    monkeypatch.setattr(workspace, "WORKSPACE_DIR", ws)
    return ws


def test_clean_workspace_removes_real_file(isolated_workspace: Path) -> None:
    (isolated_workspace / "a.txt").write_text("hello")

    workspace.clean_workspace()

    assert list(isolated_workspace.iterdir()) == []


def test_clean_workspace_removes_real_dir_recursively(
    isolated_workspace: Path,
) -> None:
    nested = isolated_workspace / "subdir"
    nested.mkdir()
    (nested / "inner.txt").write_text("inner")

    workspace.clean_workspace()

    assert not nested.exists()
    assert list(isolated_workspace.iterdir()) == []


def test_clean_workspace_does_not_follow_symlink_to_external_dir(
    isolated_workspace: Path, tmp_path: Path
) -> None:
    """A symlink-to-directory inside the workspace must be unlinked
    without touching the target.

    Pre-W15-2: ``is_dir()`` follows the link -> True -> ``shutil.rmtree``
    on the symlink raises ``OSError``, leaving the symlink in place.
    Post-W15-2: ``is_symlink()`` matches first -> ``unlink()`` removes
    just the link entry, target dir is untouched.
    """
    external = tmp_path / "external_dir"
    external.mkdir()
    (external / "victim.txt").write_text("must survive")
    (isolated_workspace / "evil_link").symlink_to(external)

    workspace.clean_workspace()

    # The symlink entry is gone (lexists checks the link itself).
    assert not (isolated_workspace / "evil_link").is_symlink()
    assert list(isolated_workspace.iterdir()) == []
    # The external target is untouched.
    assert external.exists()
    assert (external / "victim.txt").read_text() == "must survive"


def test_clean_workspace_does_not_follow_symlink_to_external_file(
    isolated_workspace: Path, tmp_path: Path
) -> None:
    """A symlink-to-file in the workspace must unlink the symlink, not
    the target. ``is_symlink()`` matches first; ``unlink()`` removes
    the link entry without dereferencing.
    """
    external = tmp_path / "external.txt"
    external.write_text("must survive")
    (isolated_workspace / "file_link").symlink_to(external)

    workspace.clean_workspace()

    assert not (isolated_workspace / "file_link").is_symlink()
    assert external.exists()
    assert external.read_text() == "must survive"


def test_clean_workspace_removes_dangling_symlink(
    isolated_workspace: Path, tmp_path: Path
) -> None:
    """A symlink whose target does not exist must still be unlinked
    without raising. Pre-W15-2 ``is_dir()`` returned False on a
    dangling symlink so this case happened to work via the
    ``child.unlink()`` fall-through; the new explicit ``is_symlink()``
    branch makes the contract intentional rather than accidental.
    """
    (isolated_workspace / "dangling").symlink_to(tmp_path / "does_not_exist")

    workspace.clean_workspace()

    assert not (isolated_workspace / "dangling").is_symlink()
    assert list(isolated_workspace.iterdir()) == []
