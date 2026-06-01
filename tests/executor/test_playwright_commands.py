from __future__ import annotations

from executor.flows.playwright.vscode import keyboard as keyboard
import pytest

from executor.flows.playwright.vscode import commands as commands


class _FakeKeyboard:
    def __init__(self) -> None:
        self.presses: list[str] = []
        self.typed: list[tuple[str, int]] = []

    def press(self, key: str) -> None:
        self.presses.append(key)

    def type(self, text: str, delay: int = 0) -> None:
        self.typed.append((text, delay))


class _FakePage:
    def __init__(self, responses: list[object]) -> None:
        self.keyboard = _FakeKeyboard()
        self._responses = list(responses)
        self.selector_calls: list[tuple[str, str | None, int | None]] = []
        self.waits: list[int] = []

    def wait_for_selector(
        self,
        selector: str,
        *,
        state: str | None = None,
        timeout: int | None = None,
    ) -> object:
        self.selector_calls.append((selector, state, timeout))
        outcome = self._responses.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def wait_for_timeout(self, ms: int) -> None:
        self.waits.append(ms)


def _timeout(message: str) -> Exception:
    return commands.PlaywrightTimeoutError(message)


def test_open_command_palette_retries_when_input_is_not_visible() -> None:
    page = _FakePage(
        [
            object(),
            _timeout("input missing"),
            _timeout("input missing"),
            _timeout("input missing"),
            object(),
            object(),
        ]
    )

    commands.open_command_palette(page)

    assert page.keyboard.presses.count(keyboard.COMMAND_PALETTE) == 2
    assert page.selector_calls[0][1] == "visible"
    assert page.selector_calls[-1][1] == "visible"


def test_run_command_supports_followup_quick_input() -> None:
    page = _FakePage(
        [
            object(),
            object(),
            object(),
            object(),
        ]
    )

    commands.run_command(
        page,
        "Debug: Open launch.json",
        expect_followup_quick_input=True,
    )

    assert page.keyboard.typed == [("Debug: Open launch.json", 30)]
    assert page.keyboard.presses[-1] == "Enter"
    assert all(state == "visible" for _, state, _ in page.selector_calls)


def test_quick_open_waits_for_hidden_visible_widget_state() -> None:
    page = _FakePage(
        [
            object(),
            object(),
            object(),
        ]
    )

    commands.quick_open(page, "src/app.py")

    assert page.keyboard.presses.count(keyboard.QUICK_OPEN) == 1
    assert page.keyboard.typed == [("src/app.py", 30)]
    assert page.selector_calls[-1][1] == "hidden"


def test_open_quick_input_raises_mode_specific_error_after_retries() -> None:
    page = _FakePage(
        [
            _timeout("missing"),
            _timeout("missing"),
        ]
    )

    with pytest.raises(commands.CommandPaletteUnavailableError) as exc_info:
        commands.open_quick_input(page, "quick_open")

    assert exc_info.value.reason_code == "quick_open_unavailable"


# --- W22 Fix 3: follow-up UI drain ------------------------------------------


class _FakeElement:
    def __init__(self, visible: bool = True) -> None:
        self._visible = visible

    def is_visible(self) -> bool:
        return self._visible


class _DrainPage:
    """Fake page modelling a stack of ``depth`` follow-up surfaces.

    Each ``Escape`` removes one layer; ``query_selector`` reports a visible
    element for ``selector`` while any layer remains. This lets us exercise the
    drain loop's dismiss/settle/recheck cycle and its ``max_depth`` bound.
    """

    def __init__(
        self, depth: int, *, selector: str = commands._QUICK_INPUT_VISIBLE
    ) -> None:
        self._remaining = depth
        self._selector = selector
        self.waits: list[int] = []
        self.escapes = 0
        self.keyboard = self  # page doubles as its own keyboard

    def press(self, key: str) -> None:
        if key == "Escape" and self._remaining > 0:
            self._remaining -= 1
            self.escapes += 1

    def query_selector(self, selector: str) -> object | None:
        if selector == self._selector and self._remaining > 0:
            return _FakeElement(True)
        return None

    def wait_for_timeout(self, ms: int) -> None:
        self.waits.append(ms)


def test_drain_followup_ui_noop_when_nothing_visible() -> None:
    page = _DrainPage(depth=0)
    assert commands.drain_followup_ui(page) == 0
    assert page.escapes == 0
    assert page.waits == []


def test_drain_followup_ui_dismisses_single_quick_input() -> None:
    page = _DrainPage(depth=1)
    assert commands.drain_followup_ui(page) == 1
    assert page.escapes == 1


def test_drain_followup_ui_dismisses_custom_dialog() -> None:
    page = _DrainPage(depth=1, selector=commands._CUSTOM_DIALOG_VISIBLE)
    assert commands.drain_followup_ui(page) == 1
    assert page.escapes == 1


def test_drain_followup_ui_respects_max_depth_bound() -> None:
    # Three stacked surfaces but max_depth=2 -> only two layers dismissed; the
    # loop stops rather than spinning on a stubborn surface.
    page = _DrainPage(depth=3)
    assert commands.drain_followup_ui(page, max_depth=2) == 2
    assert page.escapes == 2
