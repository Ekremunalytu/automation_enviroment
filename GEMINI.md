# GEMINI.md

`Last Updated: 2026-04-24`

This file was previously a near-clone of `AGENTS.md` + `AGENT_CONTEXT.md`.
It is now a thin pointer to reduce duplication drift.

## Read Path (in order)

1. [`AGENTS.md`](AGENTS.md) — authoritative rules (architectural, security,
   dependency). Read this first.
2. [`documents/AGENT_CONTEXT.md`](documents/AGENT_CONTEXT.md) — thin-context
   project map: task routing, read paths, load-only-if-needed pointers.
3. [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md) — current
   closure state, phase history, landed follow-ups.
4. Subsystem docs under [`documents/`](documents/) **only** when the task
   reaches that subsystem.

## If Docs and Code Disagree

Trust code and tests. Update the doc if the drift is confirmed.

## Context Budget

Do not scan the whole repo. Start from one lane (see AGENT_CONTEXT.md).
Ignore `extensions/`, `output/`, `node_modules/`, `__pycache__/` unless the
task explicitly targets them.
