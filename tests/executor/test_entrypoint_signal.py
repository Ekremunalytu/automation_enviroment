"""W22: the executor entrypoint installs a SIGTERM handler so an external
timeout (the analysis timeout sends SIGTERM) unwinds cleanly into
``runner.main``'s ``finally`` — which finalizes the report (Extension Host
activation parse + save) — instead of dying with the last live persist (no
activations). This pins the handler's contract.
"""

from __future__ import annotations

import signal

import pytest

from executor.flows.playwright.entrypoint import __main__ as entry_main


def test_terminate_handler_raises_systemexit_and_resets_disposition() -> None:
    original = signal.getsignal(signal.SIGTERM)
    try:
        with pytest.raises(SystemExit) as exc_info:
            entry_main._terminate_for_finalization(int(signal.SIGTERM), None)
        # 128 + signum is the conventional "terminated by signal N" exit code.
        assert exc_info.value.code == 128 + int(signal.SIGTERM)
        # Disposition reset to default so a SECOND SIGTERM hard-kills even if
        # finalization itself wedges (no infinite re-entry into the handler).
        assert signal.getsignal(signal.SIGTERM) == signal.SIG_DFL
    finally:
        signal.signal(signal.SIGTERM, original)
