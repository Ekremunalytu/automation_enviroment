"""Package entry shim for ``python -m executor.flows.playwright.entrypoint``.

Pre-W12-1 the entrypoint lived in a flat module (``entrypoint.py``) whose
``if __name__ == "__main__"`` guard ran ``main()`` directly when invoked via
``python -m``. After W12-1 ``entrypoint`` is a package, so ``python -m`` looks
for this ``__main__.py`` instead. Keep this file a one-line passthrough — all
runtime config remains in ``__init__.py::main`` (and is dispatched through
``runner.main``).
"""

from __future__ import annotations

from . import main

if __name__ == "__main__":
    main()
