"""Package entry shim for ``python -m executor.flows.playwright.entrypoint``.

Pre-W12-1 the entrypoint lived in a flat module (``entrypoint.py``) whose
``if __name__ == "__main__"`` guard ran ``main()`` directly when invoked via
``python -m``. After W12-1 ``entrypoint`` is a package, so ``python -m`` looks
for this ``__main__.py`` instead. Keep this file a one-line passthrough — all
runtime config remains in ``__init__.py::main`` (and is dispatched through
``runner.main``).
"""

from __future__ import annotations

import signal
from types import FrameType

from . import main


def _terminate_for_finalization(signum: int, frame: FrameType | None) -> None:
    """Convert an external SIGTERM into a clean unwind (W22).

    The analysis timeout terminates the executor with SIGTERM. Python's default
    SIGTERM disposition exits *without* running ``finally`` blocks, so
    ``runner.main``'s finalize (Extension Host activation parse + report save)
    never executed and the report was left with no activations. Raising
    ``SystemExit`` instead unwinds the stack through that ``finally``. Reset to
    the default disposition first so a second SIGTERM (e.g. if finalization
    itself wedges) hard-kills as before.
    """
    _ = frame
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _terminate_for_finalization)
    main()
