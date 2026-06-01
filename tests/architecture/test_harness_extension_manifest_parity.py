"""Parity gate: every command / chat participant / language-model tool the
harness registers at runtime (``extension.js`` + ``stimulus_dispatch.js``)
MUST be declared under ``contributes`` in ``package.json``.

Driving regression (field crash 2026-05-29): the W22-2 harness runtime
registered ``vscode.chat.createChatParticipant`` and
``vscode.lm.registerTool`` but ``package.json`` only contributed
``commands`` — so VS Code rejected both registrations
(``chatParticipant must be declared in package.json`` /
``Tool "<name>" was not contributed``) and the LM-tool stimulus emitted
``lm_tool_state phase=invoke_failed`` instead of ``invoked``.

A second, subtler trap this gate pins: VS Code validates the
language-model tool ``name`` and the chat participant ``name`` (the
``@``-handle) against ``/^[\\w-]+$/`` — **dots are rejected at
registration**. The id chosen in ADR 0014 (``extrace.harness.lm.tool``)
was dot-qualified and would have been silently dropped even if declared;
the valid id is ``extrace-harness-lm-tool``. See the ADR 0014
"Naming constraint" note.

The check is read-only, AST-free (regex over the JS sources + a JSON parse
of the manifest), and does not require Docker.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO_ROOT / "executor" / "flows" / "harness_extension"
PACKAGE_JSON = HARNESS_DIR / "package.json"
EXTENSION_JS = HARNESS_DIR / "extension.js"
DISPATCH_JS = HARNESS_DIR / "stimulus_dispatch.js"

# VS Code identifier validation (verified against the bundled product in
# the executor container): both the language-model tool ``name`` and the
# chat participant ``name`` must match this; dots are NOT allowed.
_VSCODE_ID_RE = re.compile(r"^[\w-]+$")
_RESERVED_TOOL_PREFIXES = ("copilot_", "vscode_")


def _manifest() -> dict:
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))


def _contributes(kind: str) -> list[dict]:
    return _manifest().get("contributes", {}).get(kind, []) or []


def _ids_from_js(call: str, *paths: Path) -> set[str]:
    """Collect the first string argument of every ``<call>("id", ...)``."""
    rx = re.compile(re.escape(call) + r"""\(\s*["']([^"']+)["']""")
    found: set[str] = set()
    for path in paths:
        found.update(rx.findall(path.read_text(encoding="utf-8")))
    return found


def test_registered_commands_are_declared() -> None:
    registered = _ids_from_js("registerCommand", EXTENSION_JS)
    declared = {entry["command"] for entry in _contributes("commands")}
    assert registered, "expected at least one registerCommand in extension.js"
    missing = sorted(registered - declared)
    assert not missing, (
        f"commands registered in extension.js but not declared in "
        f"package.json contributes.commands: {missing}"
    )


def test_registered_chat_participants_are_declared() -> None:
    registered = _ids_from_js("createChatParticipant", EXTENSION_JS)
    declared = {entry["id"] for entry in _contributes("chatParticipants")}
    assert registered, "expected a createChatParticipant call in extension.js"
    missing = sorted(registered - declared)
    assert not missing, (
        f"chat participant ids registered but not declared in "
        f"contributes.chatParticipants: {missing}"
    )


def test_registered_and_invoked_tools_are_declared() -> None:
    registered = _ids_from_js("registerTool", EXTENSION_JS)
    invoked = _ids_from_js("invokeTool", DISPATCH_JS)
    declared = {entry["name"] for entry in _contributes("languageModelTools")}
    assert registered, "expected a registerTool call in extension.js"
    missing_registered = sorted(registered - declared)
    assert not missing_registered, (
        f"tool names registered but not declared in "
        f"contributes.languageModelTools: {missing_registered}"
    )
    missing_invoked = sorted(invoked - declared)
    assert not missing_invoked, (
        f"tool names invoked in stimulus_dispatch.js but not declared "
        f"(invokeTool would raise 'was not contributed'): {missing_invoked}"
    )


def test_tool_and_participant_handles_are_vscode_valid() -> None:
    for tool in _contributes("languageModelTools"):
        name = tool["name"]
        assert _VSCODE_ID_RE.match(name), (
            f"languageModelTools name {name!r} must match /^[\\w-]+$/ — "
            "VS Code rejects dotted tool ids at registration"
        )
        assert not name.startswith(_RESERVED_TOOL_PREFIXES), (
            f"tool name {name!r} uses a reserved prefix {_RESERVED_TOOL_PREFIXES}"
        )
    for participant in _contributes("chatParticipants"):
        handle = participant["name"]
        assert _VSCODE_ID_RE.match(handle), (
            f"chatParticipant @-handle (name) {handle!r} must match "
            "/^[\\w-]+$/ — VS Code rejects dotted participant names"
        )
