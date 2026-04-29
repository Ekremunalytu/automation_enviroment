# Agent Lanes

`Last Updated: 2026-04-29`

Use these files after `AGENTS.md` and `documents/AGENT_CONTEXT.md`. Open only
the lane that matches the task.

## Lanes

- `platform-storage.md` — FastAPI platform, settings, DB, schemas, CRUD,
  migrations.
- `marketplace-analysis.md` — marketplace download/analyze flows, async jobs,
  trigger planning.
- `executor-runtime.md` — Docker executor, Playwright automation, harness,
  runtime capture, runbooks.
- `security-detection.md` — detection contracts, rules, malicious fixtures,
  security ADRs.
- `ui.md` — React/Vite analyst console, generated TS contracts, UI tests.
- `docs-maintenance.md` — documentation drift, README/ADR/runbook updates.

## Rule

Do not preload every lane. If the first lane shows the task crosses a boundary,
open the second lane explicitly and keep notes on why the expansion was needed.
