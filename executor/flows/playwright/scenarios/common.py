"""Shared helpers for Playwright automation scenarios."""

from __future__ import annotations


def log(msg: str, detail: str = "") -> None:
    suffix = f" ({detail})" if detail else ""
    print(f"[automation] {msg}{suffix}")
