"""Playwright UI helper modules for VS Code automation.

This package provides composable functions for automating VS Code UI
interactions via Playwright CDP connection. Each module has a single
responsibility (commands, editor, sidebar, terminal, panel, workspace).

Canonical invocation is `python -m executor.flows.playwright.<module>`
(see ADR 0008). The package directory name 'playwright' would shadow
the third-party `playwright` pip distribution if imported by bare name,
so dotted-form imports through the `executor` namespace are required
both inside the container and in host-side test runs.
"""
