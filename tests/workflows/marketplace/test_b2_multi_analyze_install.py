"""W26 / Stream 3 (RA2): B2 — a back-to-back analyze reaches install_extension.

B2 ("survives back-to-back use") landed direct-to-main (reset_state.py 4437d1e:
the pgrep ``--`` separator + CDP-independent needle + ``/proc`` tree reap),
unit-tested in ``tests/executor/test_reset_state.py`` and live-verified. The
roadmap B2 acceptance also asks for a lifecycle assertion that a 2nd/3rd analyze
on the SAME executor reaches ``install_extension`` with no container restart.

This pins that orchestration invariant directly: ``reset_sandbox`` ->
``install_extension`` runs cleanly back-to-back on one ``ExecutorControl``, so
analyze #2 / #3's install is never blocked by stale state left by the prior run.
(The reset SCRIPT's terminate/reap logic — the B2 fix itself — is exercised by
``test_reset_state.py``; this test pins the step sequencing the operator depends
on.)
"""

from __future__ import annotations

import threading

from appcore.contracts.schema_defs.marketplace import AnalyzeRequest
from workflows.marketplace.analysis_execution import (
    StepReporter,
    install_extension,
    reset_sandbox,
)


class _RecordingControl:
    """Records reset_sandbox + install_extension in call order (thread-safe:
    ``reset_sandbox`` runs on the off-thread coordinator)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.calls: list[str] = []
        self.installed: list[tuple[str, str, str]] = []

    def reset_sandbox(self, reload_window: bool = True) -> str:
        with self._lock:
            self.calls.append("reset_sandbox")
        return "Sandbox reset to clean baseline."

    def install_extension(self, publisher: str, name: str, version: str) -> str:
        with self._lock:
            self.calls.append("install_extension")
            self.installed.append((publisher, name, version))
        return f"Installed {publisher}.{name}@{version}."


def test_back_to_back_analyze_reaches_install_extension() -> None:
    control = _RecordingControl()
    reporter = StepReporter(None)
    request = AnalyzeRequest(publisher="ms-python", name="python", version="2025.0.0")

    # Three sequential analyses on the SAME executor control (no restart).
    for _ in range(3):
        reset_sandbox(reporter, control)
        install_extension(request, reporter, control)

    # Every analyze reset and then reached install — analyze #2 and #3 were not
    # blocked by stale state from the prior run (the B2 invariant).
    assert control.calls == [
        "reset_sandbox",
        "install_extension",
        "reset_sandbox",
        "install_extension",
        "reset_sandbox",
        "install_extension",
    ]
    assert control.installed == [("ms-python", "python", "2025.0.0")] * 3
