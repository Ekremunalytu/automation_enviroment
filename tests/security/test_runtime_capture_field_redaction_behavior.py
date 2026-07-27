"""W26 / Stream 3 (RA1, branch-review 2026-06-26): behavioral redaction of the
two sibling capture sinks the original RA1 AST gate missed.

``test_runtime_capture_field_redaction.py`` pins these structurally (the field
assignments route through ``redact_secrets``); this asserts the runtime effect —
a secret-shaped substring an analyzed extension controls is actually masked on
the persisted ``FileEvent.flags`` and the ``record_automation_event``
``LogStreamEntry``. ``redact_secrets`` is a no-op on ordinary text, so these
guard only the secret-shaped case.
"""

from __future__ import annotations

from pathlib import Path

from executor.flows.playwright import monitor


class _DummyPage:
    pass


def test_strace_file_event_flags_redacts_secret_shaped_path() -> None:
    # RA1-4: ``flags`` stores the raw strace arg blob, a strict superset of the
    # redacted ``path``. A db_url-shaped substring in a watched path must be masked
    # in BOTH path and flags on the same FileEvent — otherwise flags re-exposes,
    # on the same row, exactly what the path redaction just hid.
    line = (
        "1700000000.750 openat(AT_FDCWD, "
        '"/workspace/cfg-postgres://admin:s3cr3tpass@db.host:5432/app", '
        "O_WRONLY|O_CREAT) = 7"
    )
    event = monitor.parse_strace_file_event_line(line, monitoring_start=1700000000.0)
    assert event is not None
    assert "s3cr3tpass" not in event.flags
    assert "[REDACTED:db_url]" in event.flags
    # The path that was already redacted stays redacted (no regression).
    assert "s3cr3tpass" not in event.path
    assert "[REDACTED:db_url]" in event.path


def test_record_automation_event_redacts_extension_controlled_fields(
    tmp_path: Path,
) -> None:
    # RA1-3: activation_event flows from package.json activationEvents (extension-
    # controlled) and message embeds it. The record_automation_event LogStreamEntry
    # lands in the SAME persisted log_entries as the redacted scenario_accountant
    # path, so a malicious extension declaring a secret-shaped activationEvent must
    # not reach the persisted/UI row un-redacted.
    mon = monitor.ExtensionMonitor(_DummyPage(), report_path=str(tmp_path / "r.json"))
    attacker_event = "onCommand:Bearer eyJhbGciOiJIUzI1Ni2.abcDEF.signature123456"
    mon.record_automation_event(
        "automation_step",
        message=f"triggering {attacker_event}",
        activation_event=attacker_event,
    )
    entry = mon.report.log_entries[-1]
    assert "eyJhbGciOiJIUzI1Ni2" not in entry.activation_event
    assert "[REDACTED:bearer]" in entry.activation_event
    assert "eyJhbGciOiJIUzI1Ni2" not in entry.message
    assert "[REDACTED:bearer]" in entry.message


def test_redaction_is_a_noop_on_ordinary_capture_text(tmp_path: Path) -> None:
    # Forensic-preserving: ordinary activationEvents / paths are untouched, so the
    # redaction never degrades a normal report.
    mon = monitor.ExtensionMonitor(_DummyPage(), report_path=str(tmp_path / "r.json"))
    mon.record_automation_event(
        "automation_step",
        message="triggering onCommand:extension.run",
        activation_event="onCommand:extension.run",
    )
    entry = mon.report.log_entries[-1]
    assert entry.activation_event == "onCommand:extension.run"
    assert entry.message == "triggering onCommand:extension.run"

    line = '1700000000.750 openat(AT_FDCWD, "/workspace/.env", O_RDONLY) = 5'
    event = monitor.parse_strace_file_event_line(line, monitoring_start=1700000000.0)
    assert event is not None
    assert event.path == "/workspace/.env"
    assert "REDACTED" not in event.flags
