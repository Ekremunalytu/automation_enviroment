# CLAUDE.md

`Last Updated: 2026-06-23`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: verdict-provenance-reproducibility (Stream 3 — B5 verdict-bound-to-bytes + B6 verdict-reproducibility; the spine; week label W26) — opened on week26 (off main 27dc7f1, 2026-06-25). Closes B5+B6; ADR 0017 (Proposed) records the design, ADR 0016 gets an additive --vsix-sha256 flag. Prior stream operator-console-honesty (UI-only console-honesty) merged to main via PR #36 (week24 -> main, 1e3fba6) on 2026-06-23. Tracker: documents/active-work/W26-verdict-provenance-reproducibility.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

This file is intentionally a thin pointer. Do not duplicate phase summaries or
architecture maps here; that caused drift.

## Read Path

1. `AGENTS.md` — hard architectural and security rules.
2. `documents/AGENT_CONTEXT.md` — task-routing decision tree.
3. One matching `documents/agent-lanes/*.md` file.
4. `documents/REFACTOR_STATUS.md` (slim canonical) only when current phase
   state matters.
5. Subsystem docs only when the lane doc points to them. Slim canonicals
   link out to `documents/<area>/` splits — open the split, not the full
   canonical, for detail.
6. `documents/active-work/<file>.md` only when the lane doc points to it.

## Operating Rules

- Keep context narrow; start from one lane and do not preload
  `documents/`. Ignore generated or heavy trees unless the task
  explicitly targets them.
- If docs disagree with code/tests, trust code/tests and update the
  stale doc after confirming the drift.
- Current state is owned by `documents/REFACTOR_STATUS.md` (slim canonical).
- Deferred and pull-next work is owned by `documents/POST_POC_BACKLOG.md`
  (slim canonical).
- Phase plans live in `documents/REFACTOR_OPTIMIZATION.md`:
  W8-W13 §11 · W14 §12 · W15 §13 · W16 §14 · W17 §15 · W18 §16 ·
  W19 §17 · W20 §18 · W21 §19 · **W22 §20** (closed
  synthetically and merged to main via PR #31 `week22 -> main` `1399f82`).
- Previous named streams (reference only; active stream lives in the top
  banner): `podman-airgapped-deploy` -> `deploy/podman/README.md`
  (air-gapped Podman deploy path); the custom detection-rule stream ->
  `documents/detection-design/README.md`.
- Multi-iter roadmap source-of-truth:
  `documents/active-work/W18-W22-roadmap.md`. Past frozen trackers
  (`active-work/W{8,11,12,13,14,15,16,17,18,19,20,21,22}-*.md`) stay on
  the read path only because code/tests reference items by stable
  ID — do not renumber.
- `documents/archive/` is frozen reference; not on the default read
  path. Open only when a slim canonical explicitly points there.

## Code Intelligence (local LSP)

Symbol nav is available via the `pyright-lsp` + `typescript-lsp` Claude Code
plugins (local/user-scope, not provisioned by the repo). Prefer the LSP tool
over grep for cross-file symbol work — definitions, references, call sites —
especially the multi-touch contract/rule changes that fan out across files
(a report-contract field or a detection rule touches many files at once).

- Python cross-file resolution needs `pyrightconfig.json`
  (`{"venvPath": ".", "venv": ".venv"}`, repo root, untracked). mypy stays the
  authoritative checker; pyright only powers navigation.
- Gotcha: the first `findReferences` of a session may return same-file-only
  results — retry once. `goToDefinition` is reliable cold.
- Nav tools only, not a commit gate — pre-commit (ruff / mypy / bandit /
  `make check-all`) is unchanged. Reproduce: `claude plugin install
  pyright-lsp typescript-lsp`, then restart the session.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
