from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

from playwright.sync_api import Error as PlaywrightError  # noqa: E402

import automation  # noqa: E402


class _FakeContext:
    def __init__(self, *, closed: bool = False, raise_on_check: bool = False) -> None:
        self._closed = closed
        self._raise_on_check = raise_on_check

    def is_closed(self) -> bool:
        if self._raise_on_check:
            raise PlaywrightError("context disposed")
        return self._closed


class _FakePage:
    def __init__(
        self,
        *,
        closed: bool = False,
        raise_on_closed_check: bool = False,
        context: _FakeContext | None = None,
        probe_raises: bool = False,
    ) -> None:
        self._closed = closed
        self._raise_on_closed_check = raise_on_closed_check
        self.context = context or _FakeContext()
        self._probe_raises = probe_raises
        self.wait_for_function_calls: list[tuple[str, int]] = []

    def is_closed(self) -> bool:
        if self._raise_on_closed_check:
            raise PlaywrightError("page disposed")
        return self._closed

    def wait_for_function(self, expression: str, *, timeout: int = 0) -> None:
        self.wait_for_function_calls.append((expression, timeout))
        if self._probe_raises:
            raise PlaywrightError("probe failed")


def test_is_fatal_recognizes_target_crashed() -> None:
    exc = PlaywrightError("Keyboard.press: Target crashed")
    fatal, reason = automation.is_fatal_ui_error(exc, _FakePage())
    assert (fatal, reason) == (True, "fatal_ui_crash")


def test_is_fatal_recognizes_renderer_process_gone() -> None:
    exc = PlaywrightError("CodeWindow: renderer process gone, code: 5")
    fatal, reason = automation.is_fatal_ui_error(exc, _FakePage())
    assert fatal is True
    assert reason == "fatal_ui_crash"


def test_is_fatal_recognizes_closed_browser_message() -> None:
    exc = PlaywrightError("Target page, context or browser has been closed")
    fatal, _ = automation.is_fatal_ui_error(exc, _FakePage())
    assert fatal is True


def test_is_fatal_recognizes_connection_closed() -> None:
    exc = PlaywrightError("Connection closed")
    fatal, _ = automation.is_fatal_ui_error(exc, _FakePage())
    assert fatal is True


def test_is_fatal_recognizes_closed_page_via_is_closed() -> None:
    page = _FakePage(closed=True)
    exc = PlaywrightError("clicking selector timed out")
    fatal, reason = automation.is_fatal_ui_error(exc, page)
    assert (fatal, reason) == (True, "fatal_ui_crash")


def test_is_fatal_recognizes_closed_context() -> None:
    page = _FakePage(context=_FakeContext(closed=True))
    exc = RuntimeError("selector not found")
    fatal, _ = automation.is_fatal_ui_error(exc, page)
    assert fatal is True


def test_is_fatal_recognizes_probe_raise() -> None:
    page = _FakePage(probe_raises=True)
    exc = RuntimeError("some transient error")
    fatal, _ = automation.is_fatal_ui_error(exc, page)
    assert fatal is True
    assert page.wait_for_function_calls, "liveness probe should have been invoked"


def test_is_fatal_treats_page_api_raise_as_fatal() -> None:
    page = _FakePage(raise_on_closed_check=True)
    exc = RuntimeError("minor error")
    fatal, _ = automation.is_fatal_ui_error(exc, page)
    assert fatal is True


def test_is_fatal_ignores_transient_timeout_on_live_page() -> None:
    page = _FakePage()
    exc = PlaywrightError("Timeout 30000ms exceeded while waiting for selector")
    fatal, reason = automation.is_fatal_ui_error(exc, page)
    assert (fatal, reason) == (False, "")
    assert page.wait_for_function_calls, "probe should confirm liveness"


def test_is_fatal_handles_none_page() -> None:
    exc = RuntimeError("editor crash but we have no page handle")
    fatal, reason = automation.is_fatal_ui_error(exc, None)
    assert (fatal, reason) == (False, "")


def test_is_fatal_handles_non_playwright_exceptions() -> None:
    exc = ValueError("not a playwright error")
    page = _FakePage()
    fatal, _ = automation.is_fatal_ui_error(exc, page)
    assert fatal is False
