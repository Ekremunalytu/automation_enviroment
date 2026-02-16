from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = Path(__file__).resolve().parents[2] / "executor" / "playwright"
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import monitor  # noqa: E402


def test_parse_activations_from_log_respects_start_offset(tmp_path: Path) -> None:
    log_file = tmp_path / "exthost.log"
    old_line = "activating extension 'old.publisher' because of 'onLanguage:python'\n"
    new_line = "activating extension 'new.publisher' because of 'onCommand:test'\n"
    log_file.write_text(old_line + new_line)

    start_offset = len(old_line.encode("utf-8"))
    entries = monitor.parse_activations_from_log(log_file, start_offset=start_offset)

    assert [entry.extension_id for entry in entries] == ["new.publisher"]
    assert entries[0].activation_event == "onCommand:test"


def test_parse_all_exthost_logs_uses_per_file_offsets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_log = tmp_path / "first.log"
    second_log = tmp_path / "second.log"

    first_old = "activating extension 'first.old' because of 'onStartupFinished'\n"
    first_new = "activating extension 'first.new' because of 'onView:explorer'\n"
    second_line = "activating extension 'second.ext' because of 'onLanguage:json'\n"

    first_log.write_text(first_old + first_new)
    second_log.write_text(second_line)

    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [first_log, second_log])

    offsets = {
        str(first_log.resolve()): len(first_old.encode("utf-8")),
    }
    entries = monitor.parse_all_exthost_logs(start_offsets=offsets)

    assert [entry.extension_id for entry in entries] == ["first.new", "second.ext"]
