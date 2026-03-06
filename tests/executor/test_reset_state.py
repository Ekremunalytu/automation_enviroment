from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = Path(__file__).resolve().parents[2] / "executor" / "playwright"
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import reset_state  # noqa: E402


def test_reset_executor_state_clears_extensions_and_logs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    extensions_dir = tmp_path / "extensions"
    logs_dir = tmp_path / "logs"
    workspace_dir = tmp_path / "workspace"

    extensions_dir.mkdir()
    logs_dir.mkdir()
    workspace_dir.mkdir()

    (extensions_dir / "old-extension").mkdir()
    (extensions_dir / "note.txt").write_text("leftover")
    (logs_dir / "session-1").mkdir()
    (logs_dir / "latest").symlink_to(logs_dir / "session-1", target_is_directory=True)

    call_order: list[str] = []

    def fake_clean_workspace() -> None:
        call_order.append("clean")
        (workspace_dir / "scratch.txt").write_text("temp")

    def fake_setup_dev_environment() -> None:
        call_order.append("setup")
        (workspace_dir / "seed.txt").write_text("restored")

    monkeypatch.setattr(reset_state, "EXTENSIONS_DIR", extensions_dir)
    monkeypatch.setattr(reset_state, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(reset_state.workspace, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(reset_state.workspace, "clean_workspace", fake_clean_workspace)
    monkeypatch.setattr(
        reset_state.workspace,
        "setup_dev_environment",
        fake_setup_dev_environment,
    )

    summary = reset_state.reset_executor_state()

    assert summary == {"removed_extensions": 2, "removed_logs": 2}
    assert call_order == ["clean", "setup"]
    assert sorted(path.name for path in extensions_dir.iterdir()) == []
    assert sorted(path.name for path in logs_dir.iterdir()) == []
    assert (workspace_dir / "seed.txt").read_text() == "restored"
