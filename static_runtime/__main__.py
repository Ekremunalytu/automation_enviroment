"""Package entry shim: ``python -m static_runtime`` -> ``entrypoint.main()``.

Parallels ``executor.flows.playwright.entrypoint`` package-mode invocation.
"""

from __future__ import annotations

from static_runtime.entrypoint import main

if __name__ == "__main__":
    raise SystemExit(main())
