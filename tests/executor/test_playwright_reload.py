from __future__ import annotations

from types import SimpleNamespace

import pytest

from executor.flows.playwright import reload_vscode, vscode


class _FakeSyncPlaywright:
    def __enter__(self) -> object:
        return SimpleNamespace()

    def __exit__(self, exc_type, exc, exc_tb) -> bool:
        return False


def test_reload_window_closes_browser_on_success(monkeypatch) -> None:
    browser = SimpleNamespace()
    page = object()
    disconnect_calls: list[object] = []
    reload_calls: list[tuple[object, object, int, object]] = []

    monkeypatch.setattr(reload_vscode, "sync_playwright", lambda: _FakeSyncPlaywright())
    monkeypatch.setattr(
        reload_vscode.vscode,
        "connect_to_ready_workbench",
        lambda _playwright, *, timeout_ms=30_000, log=None: (browser, page),
    )
    monkeypatch.setattr(
        reload_vscode.vscode,
        "reload_workbench_window",
        lambda current_browser, current_page, *, reconnect_timeout_ms=30_000, log=None: (
            reload_calls.append(
                (current_browser, current_page, reconnect_timeout_ms, log)
            )
        ),
    )
    monkeypatch.setattr(
        reload_vscode.vscode,
        "disconnect",
        lambda current_browser: disconnect_calls.append(current_browser),
    )

    reload_vscode.reload_window()

    assert reload_calls == [(browser, page, reload_vscode._RELOAD_TIMEOUT_MS, print)]
    assert disconnect_calls == [browser]


def test_reload_window_closes_browser_on_failure(monkeypatch) -> None:
    browser = SimpleNamespace()
    page = object()
    disconnect_calls: list[object] = []

    monkeypatch.setattr(reload_vscode, "sync_playwright", lambda: _FakeSyncPlaywright())
    monkeypatch.setattr(
        reload_vscode.vscode,
        "connect_to_ready_workbench",
        lambda _playwright, *, timeout_ms=30_000, log=None: (browser, page),
    )
    monkeypatch.setattr(
        reload_vscode.vscode,
        "reload_workbench_window",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            vscode.ReloadWindowError(
                "reconnect",
                "Timed out while reconnecting to a VS Code workbench page.",
            )
        ),
    )
    monkeypatch.setattr(
        reload_vscode.vscode,
        "disconnect",
        lambda current_browser: disconnect_calls.append(current_browser),
    )

    with pytest.raises(
        vscode.ReloadWindowError,
        match="reconnect: Timed out while reconnecting to a VS Code workbench page",
    ):
        reload_vscode.reload_window()

    assert disconnect_calls == [browser]


def test_main_returns_nonzero_for_reload_window_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        reload_vscode,
        "reload_window",
        lambda: (_ for _ in ()).throw(
            vscode.ReloadWindowError("reconnect", "workbench missing")
        ),
    )

    assert reload_vscode.main() == 1
    captured = capsys.readouterr()
    assert "[reload] ERROR reconnect: workbench missing" in captured.err
