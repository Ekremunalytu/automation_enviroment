"""Package entry shim for ``python -m executor.flows.playwright.workspace``.

Pre-W12-1 the honeypot seeder lived in a flat module (``workspace.py``)
whose ``if __name__ == "__main__"`` guard ran ``setup_dev_environment()``
directly under ``python -m``. After W12-1 ``workspace`` is a package, and
Python's ``-m`` semantics look for ``__main__.py`` (not the package's
``__init__.py`` guard) — so without this shim ``executor/container/start.sh``
fails container boot with ``No module named ...workspace.__main__``.
"""

from __future__ import annotations

from . import setup_dev_environment

if __name__ == "__main__":
    print("[*] Setting up developer environment...")
    setup_dev_environment()
    print("[+] Environment ready: .env, SSH keys, AWS creds, source code, etc.")
