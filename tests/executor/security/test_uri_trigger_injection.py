"""W8-3 security regression: URI trigger argv-form invocation + scheme allow-list.

Covers three layers:

1. ``validate_uri_scheme`` — accepts the four allow-listed schemes,
   rejects every other scheme plus malformed inputs.
2. ``run_uri_trigger`` — calls ``subprocess.run`` with an argv list and
   the absolute path to ``xdg-open``; never invokes a shell.
3. Call-site integration — ``entrypoint_triggers.run_extra_triggers`` and
   ``stimulus_attempts.execute_attempt(extra:uri_trigger)`` reject
   adversarial URIs before any terminal stimulus or subprocess fires.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[3] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import entrypoint_triggers  # noqa: E402
import stimulus_attempts  # noqa: E402
import triggers as trigger_loader  # noqa: E402
import uri_validation  # noqa: E402


# ---------------------------------------------------------------------------
# validate_uri_scheme
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "uri",
    [
        "vscode://publisher.tool/activate",
        "vscode-insiders://publisher.tool/activate",
        "http://example.com/path",
        "https://example.com/path?query=1",
    ],
)
def test_validate_uri_scheme_accepts_allowlist(uri: str) -> None:
    assert uri_validation.validate_uri_scheme(uri) == uri


@pytest.mark.parametrize(
    "uri",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/plain,payload",
        "ftp://example.com/x",
        "",
        "no-scheme-here",
        "; rm -rf /",
        "$(whoami)",
        "vscode://x'; rm -rf /; echo '",  # scheme is allow-listed but injection
    ],
)
def test_validate_uri_scheme_rejects_disallowed_or_malformed(uri: str) -> None:
    if uri.startswith("vscode://"):
        # The four-token injection retains scheme=vscode and is allow-listed.
        # This branch documents that scheme validation alone is not the
        # whole defence — argv-form invocation handles the residual risk.
        assert uri_validation.validate_uri_scheme(uri) == uri
        return
    with pytest.raises(uri_validation.UriValidationError):
        uri_validation.validate_uri_scheme(uri)


def test_uri_validation_error_is_value_error_subclass() -> None:
    """Caller exception clauses written for ``ValueError`` (the legacy
    contract) keep working without per-class fan-out."""
    assert issubclass(uri_validation.UriValidationError, ValueError)


# ---------------------------------------------------------------------------
# run_uri_trigger — argv-form proof
# ---------------------------------------------------------------------------


def test_run_uri_trigger_invokes_subprocess_with_argv_list_and_absolute_path(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    uri_validation.run_uri_trigger("vscode://publisher.tool/activate")

    assert captured["argv"] == [
        uri_validation.XDG_OPEN_PATH,
        "vscode://publisher.tool/activate",
    ]
    assert captured["argv"][0].startswith("/")  # absolute binary path
    assert captured["kwargs"]["check"] is False
    assert captured["kwargs"]["timeout"] == uri_validation.DEFAULT_TIMEOUT_S
    # Critically: no shell=True, no string command form.
    assert "shell" not in captured["kwargs"] or captured["kwargs"]["shell"] is False


def test_run_uri_trigger_validates_before_subprocess(monkeypatch) -> None:
    """A rejected URI must raise without ever reaching ``subprocess.run``."""
    invocations: list[Any] = []

    def fake_run(argv, **kwargs):
        invocations.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    with pytest.raises(uri_validation.UriValidationError):
        uri_validation.run_uri_trigger("file:///etc/passwd")
    assert invocations == []


# ---------------------------------------------------------------------------
# entrypoint_triggers.run_extra_triggers — adversarial URI integration
# ---------------------------------------------------------------------------


class _FakeKeyboard:
    def press(self, key: str) -> None:
        _ = key

    def type(self, text: str, delay: int | None = None) -> None:
        _ = (text, delay)


class _FakePage:
    def __init__(self) -> None:
        self.keyboard = _FakeKeyboard()

    def wait_for_timeout(self, timeout_ms: int) -> None:
        _ = timeout_ms

    def wait_for_selector(self, selector, state="visible", timeout=0):
        _ = (selector, state, timeout)
        return None


def _build_deps(calls: list[tuple[str, Any]]) -> SimpleNamespace:
    """Return a deps namespace whose terminal/editor calls record into ``calls``.

    The expectation under test is that an adversarial URI never reaches
    these helpers because validation fails first.
    """
    terminal = SimpleNamespace(
        new_terminal=lambda page: calls.append(("new_terminal", None)),
        type_in_terminal=lambda page, text: calls.append(("type_terminal", text)),
    )
    editor = SimpleNamespace(
        open_file_by_name=lambda page, filename: calls.append(("open_file", filename)),
        close_active_editor=lambda page: calls.append(("close_editor", None)),
        _dismiss_notification=lambda page: "",
    )
    return SimpleNamespace(terminal=terminal, editor=editor)


@pytest.mark.parametrize(
    "uri",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/plain,payload",
        "; rm -rf /home/executor",
        "no-scheme-here",
    ],
)
def test_run_extra_triggers_rejects_adversarial_uri_before_terminal(
    monkeypatch, uri: str
) -> None:
    payload = trigger_loader.TriggerPayload(uri_trigger=uri)
    calls: list[tuple[str, Any]] = []
    deps = _build_deps(calls)

    invocations: list[Any] = []

    def fake_run(argv, **kwargs):
        invocations.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)

    failed = entrypoint_triggers.run_extra_triggers(_FakePage(), payload, deps=deps)

    assert failed == ["uri_trigger"]
    # The adversarial URI must short-circuit before terminal stimulus and
    # before any subprocess invocation.
    assert ("new_terminal", None) not in calls
    assert ("type_terminal", uri) not in calls
    assert all(name != "type_terminal" for name, _ in calls)
    assert invocations == []


def test_run_extra_triggers_argv_form_under_valid_uri(monkeypatch) -> None:
    payload = trigger_loader.TriggerPayload(
        uri_trigger="vscode://publisher.tool/activate"
    )
    calls: list[tuple[str, Any]] = []
    deps = _build_deps(calls)

    captured_argv: list[Any] = []

    def fake_run(argv, **kwargs):
        captured_argv.append(argv)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)

    failed = entrypoint_triggers.run_extra_triggers(_FakePage(), payload, deps=deps)

    assert failed == []
    assert captured_argv == [
        [uri_validation.XDG_OPEN_PATH, "vscode://publisher.tool/activate"],
    ]
    assert ("new_terminal", None) in calls
    # type_in_terminal must NOT be invoked any more — argv-form replaces it.
    assert all(name != "type_terminal" for name, _ in calls)


# ---------------------------------------------------------------------------
# stimulus_attempts.execute_attempt(extra:uri_trigger) — adversarial path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "uri",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/plain,payload",
        "ftp://evil.example/exfil",
    ],
)
def test_execute_attempt_uri_trigger_rejects_adversarial_uri(
    monkeypatch, uri: str
) -> None:
    captured_terminal_calls: list[tuple[str, Any]] = []
    monkeypatch.setattr(
        stimulus_attempts.terminal,
        "new_terminal",
        lambda page: captured_terminal_calls.append(("new_terminal", None)),
    )
    monkeypatch.setattr(
        stimulus_attempts.terminal,
        "type_in_terminal",
        lambda page, text: captured_terminal_calls.append(("type_terminal", text)),
    )
    captured_subprocess_calls: list[Any] = []
    monkeypatch.setattr(
        uri_validation.subprocess,
        "run",
        lambda argv, **kwargs: captured_subprocess_calls.append((argv, kwargs)),
    )

    payload = SimpleNamespace(uri_trigger=uri)
    attempt: dict[str, Any] = {"activation_event": "onUri"}

    with pytest.raises(uri_validation.UriValidationError):
        stimulus_attempts.execute_attempt(
            _FakePage(),
            payload,
            attempt,
            action="extra:uri_trigger",
            trigger_method="uri",
            result=SimpleNamespace(),
            monitor=None,
        )

    # Terminal helpers must not fire on an adversarial URI.
    assert captured_terminal_calls == []
    assert captured_subprocess_calls == []


# ---------------------------------------------------------------------------
# validate_uri_scheme — defensive contract gaps
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("non_string", [None, 123, 1.5, [], {}, True, b"vscode://x"])
def test_validate_uri_scheme_rejects_non_string_input(non_string: Any) -> None:
    """The helper's ``isinstance(uri, str)`` guard must reject any
    non-string input with ``UriValidationError`` so a caller that
    forwards an unparsed payload (e.g. a Pydantic ``Any`` slot) cannot
    bypass scheme validation."""
    with pytest.raises(uri_validation.UriValidationError):
        uri_validation.validate_uri_scheme(non_string)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "uri",
    [
        "VSCODE://publisher.tool/activate",
        "Vscode://publisher.tool/activate",
        "VSCode-Insiders://publisher.tool/activate",
        "HTTPS://example.com/path",
        "Http://example.com/path",
    ],
)
def test_validate_uri_scheme_accepts_case_insensitive_scheme(uri: str) -> None:
    """RFC 3986 schemes are case-insensitive. The helper lower-cases the
    parsed scheme before allow-list lookup; this test pins that behaviour
    so a future refactor cannot silently tighten the contract."""
    assert uri_validation.validate_uri_scheme(uri) == uri


# ---------------------------------------------------------------------------
# run_uri_trigger — exception propagation
# ---------------------------------------------------------------------------


def test_run_uri_trigger_propagates_subprocess_timeout(monkeypatch) -> None:
    """If ``xdg-open`` hangs past ``timeout_s`` the helper must propagate
    ``subprocess.TimeoutExpired`` so the caller's catch clause records a
    failed trigger. Silent swallow would hide a real problem."""

    def fake_run(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout", 0.0))

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    with pytest.raises(subprocess.TimeoutExpired):
        uri_validation.run_uri_trigger("vscode://publisher.tool/activate")


def test_run_uri_trigger_propagates_oserror_when_binary_missing(monkeypatch) -> None:
    """If ``/usr/bin/xdg-open`` is absent inside the container,
    ``subprocess.run`` raises ``FileNotFoundError`` (subclass of
    ``OSError``); the helper must let it propagate to the caller's
    failure path."""

    def fake_run(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    with pytest.raises(FileNotFoundError):
        uri_validation.run_uri_trigger("vscode://publisher.tool/activate")


# ---------------------------------------------------------------------------
# entrypoint_triggers.run_extra_triggers — failure-path coverage
# ---------------------------------------------------------------------------


def test_run_extra_triggers_marks_failed_when_subprocess_times_out(monkeypatch) -> None:
    """A valid URI whose argv-form launch raises ``TimeoutExpired`` must
    surface as ``failed_triggers=["uri_trigger"]``; this exercises the
    widened except clause that now includes ``subprocess.SubprocessError``
    alongside ``PlaywrightError``/``RuntimeError``."""
    payload = trigger_loader.TriggerPayload(
        uri_trigger="vscode://publisher.tool/activate"
    )
    calls: list[tuple[str, Any]] = []
    deps = _build_deps(calls)

    def fake_run(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout", 0.0))

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    failed = entrypoint_triggers.run_extra_triggers(_FakePage(), payload, deps=deps)

    assert failed == ["uri_trigger"]


def test_run_extra_triggers_marks_failed_when_binary_missing(monkeypatch) -> None:
    """Same coverage point but for the ``OSError`` branch of the except
    clause: an absent ``xdg-open`` binary must record the trigger as
    failed instead of crashing the run."""
    payload = trigger_loader.TriggerPayload(
        uri_trigger="vscode://publisher.tool/activate"
    )
    calls: list[tuple[str, Any]] = []
    deps = _build_deps(calls)

    def fake_run(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    failed = entrypoint_triggers.run_extra_triggers(_FakePage(), payload, deps=deps)

    assert failed == ["uri_trigger"]


def test_run_extra_triggers_emits_failed_event_on_adversarial_uri(monkeypatch) -> None:
    """Adversarial URI rejection must propagate to the recorder so the
    final report carries an ``extra_trigger ... failed`` event tied to
    ``activation_event="onUri"`` — operators reading the report would
    otherwise see a silent miss."""
    payload = trigger_loader.TriggerPayload(uri_trigger="javascript:alert(1)")
    calls: list[tuple[str, Any]] = []
    deps = _build_deps(calls)
    events: list[tuple[str, str, str, str, str]] = []

    def record_event(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        events.append((kind, message, status, scenario_name, activation_event))

    monkeypatch.setattr(
        uri_validation.subprocess,
        "run",
        lambda argv, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    failed = entrypoint_triggers.run_extra_triggers(
        _FakePage(),
        payload,
        deps=deps,
        automation_event_recorder=record_event,
    )

    assert failed == ["uri_trigger"]
    failed_events = [e for e in events if e[2] == "failed" and e[4] == "onUri"]
    assert len(failed_events) == 1
    assert "URI trigger failed" in failed_events[0][1]


# ---------------------------------------------------------------------------
# stimulus_attempts.execute_attempt(extra:uri_trigger) — happy + legacy paths
# ---------------------------------------------------------------------------


def test_execute_attempt_uri_trigger_invokes_argv_form_under_valid_uri(
    monkeypatch,
) -> None:
    """Mirror of the entrypoint_triggers happy-path argv-form proof for
    the ``execute_attempt(extra:uri_trigger)`` branch — pins that this
    code path also goes through ``uri_validation.run_uri_trigger`` and
    not through the legacy terminal interpolation."""
    captured_terminal_calls: list[tuple[str, Any]] = []
    monkeypatch.setattr(
        stimulus_attempts.terminal,
        "new_terminal",
        lambda page: captured_terminal_calls.append(("new_terminal", None)),
    )
    monkeypatch.setattr(
        stimulus_attempts.terminal,
        "type_in_terminal",
        lambda page, text: captured_terminal_calls.append(("type_terminal", text)),
    )
    captured_argv: list[Any] = []

    def fake_run(argv, **kwargs):
        captured_argv.append(argv)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(uri_validation.subprocess, "run", fake_run)
    completed_wait = SimpleNamespace(status="completed", message="ok")
    monkeypatch.setattr(
        stimulus_attempts, "wait_for_ui_settle", lambda *a, **k: completed_wait
    )
    monkeypatch.setattr(
        stimulus_attempts, "wait_for_trigger_effect", lambda *a, **k: completed_wait
    )

    payload = SimpleNamespace(uri_trigger="vscode://publisher.tool/activate")
    attempt: dict[str, Any] = {"activation_event": "onUri"}

    stimulus_attempts.execute_attempt(
        _FakePage(),
        payload,
        attempt,
        action="extra:uri_trigger",
        trigger_method="uri",
        result=SimpleNamespace(),
        monitor=None,
    )

    assert captured_argv == [
        [uri_validation.XDG_OPEN_PATH, "vscode://publisher.tool/activate"],
    ]
    # new_terminal still fires (UI sequencing preserved); type_in_terminal
    # is the legacy shell-template entry and must NOT.
    assert ("new_terminal", None) in captured_terminal_calls
    assert all(name != "type_terminal" for name, _ in captured_terminal_calls)


@pytest.mark.parametrize("empty_uri", ["", "   ", "\t\n"])
def test_execute_attempt_uri_trigger_empty_uri_raises_plain_value_error(
    monkeypatch, empty_uri: str
) -> None:
    """Legacy contract: an empty/whitespace-only ``uri_trigger`` raises a
    plain ``ValueError`` (not ``UriValidationError``) so callers that
    discriminate on exception type keep their behaviour. The strip+empty
    guard sits before ``validate_uri_scheme`` and must not be bypassed."""
    monkeypatch.setattr(stimulus_attempts.terminal, "new_terminal", lambda page: None)
    monkeypatch.setattr(
        uri_validation.subprocess,
        "run",
        lambda argv, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    payload = SimpleNamespace(uri_trigger=empty_uri)
    attempt: dict[str, Any] = {"activation_event": "onUri"}

    with pytest.raises(ValueError) as exc_info:
        stimulus_attempts.execute_attempt(
            _FakePage(),
            payload,
            attempt,
            action="extra:uri_trigger",
            trigger_method="uri",
            result=SimpleNamespace(),
            monitor=None,
        )
    # Must be the plain ValueError from the empty-URI guard, not the
    # ``UriValidationError`` subclass produced by scheme validation.
    assert type(exc_info.value) is ValueError
    assert "without a target URI" in str(exc_info.value)
