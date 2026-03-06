from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import workspace  # noqa: E402


def test_create_bait_files_uses_active_workspace(monkeypatch, tmp_path: Path) -> None:
    """Custom-editor bait files should be created inside WORKSPACE_DIR."""
    monkeypatch.setattr(workspace, "WORKSPACE_DIR", tmp_path / "workspace")

    created = workspace.create_bait_files(["custom/file.test", "second.txt"])

    assert created == [
        workspace.WORKSPACE_DIR / "custom/file.test",
        workspace.WORKSPACE_DIR / "second.txt",
    ]
    assert (workspace.WORKSPACE_DIR / "custom/file.test").exists()
    assert (workspace.WORKSPACE_DIR / "second.txt").exists()
