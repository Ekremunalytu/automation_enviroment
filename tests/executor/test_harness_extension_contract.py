"""Contract checks for the VS Code harness extension shims."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROVIDERS_PATH = ROOT / "executor/flows/harness_extension/providers.js"


def test_harness_providers_expose_vscode_event_contracts() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for harness extension contract checks")

    script = f"""
const assert = require("node:assert/strict");
const Module = require("node:module");
const originalLoad = Module._load;
const fired = [];
const vscode = {{
  EventEmitter: class {{
    constructor() {{
      this.event = (listener) => {{
        this.listener = listener;
        return {{ dispose() {{}} }};
      }};
    }}
    fire(value) {{
      fired.push(value);
      if (this.listener) {{
        this.listener(value);
      }}
    }}
  }},
  Disposable: class {{
    constructor(dispose) {{
      this.dispose = dispose;
    }}
  }},
  FileChangeType: {{ Changed: 1, Deleted: 2 }},
  FileType: {{ File: 1 }},
}};
Module._load = function load(request, parent, isMain) {{
  if (request === "vscode") {{
    return vscode;
  }}
  return originalLoad.call(this, request, parent, isMain);
}};
const {{ LocalAuthProvider, LocalFileSystemProvider }} = require({str(PROVIDERS_PATH)!r});

const authProvider = new LocalAuthProvider();
assert.equal(typeof authProvider.onDidChangeSessions, "function");
authProvider.onDidChangeSessions(() => {{}});
authProvider.createSession(["default"]);

const fsProvider = new LocalFileSystemProvider();
assert.equal(typeof fsProvider.onDidChangeFile, "function");
fsProvider.onDidChangeFile(() => {{}});
fsProvider.writeFile({{ path: "/sample" }});
fsProvider.rename({{ path: "/sample" }}, {{ path: "/renamed" }});
fsProvider.delete({{ path: "/renamed" }});
assert.ok(fired.length >= 4);
"""
    subprocess.run([node, "-e", script], check=True, text=True, timeout=10)  # noqa: S603
