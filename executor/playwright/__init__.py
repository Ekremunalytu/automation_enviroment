"""Playwright UI helper modules for VS Code automation.

This package provides composable functions for automating VS Code UI
interactions via Playwright CDP connection. Each module has a single
responsibility (commands, editor, sidebar, terminal, panel, workspace).

Note: Due to the directory name 'playwright' conflicting with the pip
package, these modules are imported directly (not as a package) when
run via entrypoint.py inside the executor container.
"""
