"""Capability taxonomy and per-track support matrices.

W10-3 split from former monolithic ``registry.py``. Pure data; no behavior.
"""

from __future__ import annotations

CAPABILITY_TAXONOMY: list[str] = [
    "commands",
    "window_ui",
    "workspace_fs",
    "languages_editor",
    "debug",
    "terminal_tasks",
    "scm",
    "search_views",
    "settings",
    "notebooks",
    "custom_editors",
    "uri_walkthrough",
    "authentication",
    "chat",
    "comments",
    "testing",
    "webview",
    "workspace_trust",
]

_GLOBAL_CAPABILITY_SUPPORT: dict[str, str] = {
    "commands": "covered",
    "window_ui": "covered",
    "workspace_fs": "covered",
    "languages_editor": "covered",
    "debug": "covered",
    "terminal_tasks": "covered",
    "scm": "covered",
    "search_views": "covered",
    "settings": "covered",
    "notebooks": "covered",
    "custom_editors": "covered",
    "uri_walkthrough": "covered",
    "authentication": "covered",
    "chat": "covered",
    "comments": "covered",
    "testing": "covered",
    "webview": "covered",
    "workspace_trust": "covered",
}

_GLOBAL_CAPABILITY_NOTES: dict[str, str] = {
    "custom_editors": (
        "Custom editor coverage uses bait files plus a post-open ledger so each "
        "attempt is visible even when the target editor fails to restore."
    ),
    "uri_walkthrough": (
        "URI, walkthrough, and open-external flows are kept explicit in the "
        "ledger so UI-first vs harness-assisted attempts stay distinguishable."
    ),
    "authentication": (
        "Authentication coverage stays local-only and uses stub providers or "
        "target provider requests inside the sandbox."
    ),
    "chat": (
        "Chat participant and language-model tool coverage remain local-only and "
        "must not call external services."
    ),
    "comments": (
        "Comment thread coverage is provided through local harness surfaces so "
        "discussion flows stay inside the sandbox."
    ),
    "testing": (
        "Testing coverage uses local controllers and run/debug flows without "
        "calling external test services."
    ),
    "workspace_trust": (
        "Workspace trust transitions are explicitly labeled when they require "
        "harness assistance instead of visible UI-only stimulation."
    ),
}

_OFFICIAL_CAPABILITY_SUPPORT: dict[str, str] = {
    "commands": "covered",
    "window_ui": "covered",
    "workspace_fs": "covered",
    "languages_editor": "covered",
    "debug": "covered",
    "terminal_tasks": "covered",
    "scm": "covered",
    "search_views": "covered",
    "settings": "covered",
    "notebooks": "covered",
    "custom_editors": "covered",
    "uri_walkthrough": "covered",
    "authentication": "covered",
    "chat": "covered",
    "comments": "covered",
    "testing": "covered",
    "webview": "covered",
    "workspace_trust": "covered",
}

_HEURISTIC_CAPABILITY_SUPPORT: dict[str, str] = {
    capability: _GLOBAL_CAPABILITY_SUPPORT[capability]
    for capability in CAPABILITY_TAXONOMY
}

_OFFICIAL_TRACK = "official"
_HEURISTIC_TRACK = "heuristic"
_TRACK_SOURCE = {
    _OFFICIAL_TRACK: "official_activation_track",
    _HEURISTIC_TRACK: "heuristic_workflow_track",
}
