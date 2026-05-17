# CLAUDE.md

`Last Updated: 2026-05-17 (W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d — W14-1..W14-8 sub-iter slate + post-slate hotfixes + close-out hygiene pass (Ruff lint, UI contract sync, markdown formatting, doc truth-state alignment) and new regression gates (make markdownlint + ADR code fence arch test + executor container shipping + Python 3.11+ API gate); W15 active on week15 branch cut from main HEAD 7cc2921 on 2026-05-14; W15-1 closed via c58c365 — sync analyze error taxonomy parity (M10); W15-2 closed via 765cde7 — clean_workspace is_symlink-before-rmtree (M12); W15-3 closed via 3512a7c — activationEvents bounds + Alembic field-length migration (U8); W15-4 closed via 89e13e3 — UI bounds bundle (timeline/density/relations graph caps, U1/U2/U3 + U6); W15-5 closed 2026-05-17 via 43d6438 — quick fixes bundle: UI /health proxy I2 + lifecycle for <id> regex I4; W15-6 closed 2026-05-17 via be52520 — ADR 0011 unauthenticated catalog endpoints posture Accepted and implemented (Option A; Proposed at e41722e; new tests/architecture/test_catalog_endpoint_posture.py gate with 3 AST invariants; ADR 0002 NOT amended); W15-1 post-slate typing hotfix via 976dc96 — ANALYZE_ERROR_TYPES annotation BaseException -> Exception narrowing; W15-7 closed 2026-05-17 — compose image SHA pin via 54e7a93 (postgres:16-alpine + alpine/socat:1.8.0.3 manifest digest pin) + test extension via 7ebbbfb (test_dockerfile_digest_pin.py compose image: scope; tests/architecture/ 196 → 198 passing, +2 W15-7 gates) + GH action trivy version pin via 452f1a1 (aquasecurity/trivy-action@v0.36.0) + final preamble refresh; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3; W15 mid-iter hygiene 2026-05-16: doc-preamble consistency arch gate added + 3 new audit findings appended to POST_POC_BACKLOG — health-reconciliation-responsibility-split, marketplace-router-test-suite-split, analysis-job-worker-entry-crud-ownership)`

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
- W8-W13 planning is owned by `documents/REFACTOR_OPTIMIZATION.md` section 11;
  W14 by section 12; W15 by section 13. W13 closed `2026-05-13`; PR #20
  `week13 -> main` merged via `772deb3`. **W14 closed `2026-05-14` and
  merged via PR #21 (`4e03c8d`)** — W14-1..W14-6 sub-iter slate +
  post-slate hotfixes W14-7/W14-8 + close-out hygiene pass (Ruff lint,
  UI contract sync, markdown formatting, doc truth-state alignment,
  new regression gates: `make markdownlint`, ADR code fence arch test).
  **Active phase: W15 — Codex U-class Close-Out + UI Bounds + Posture**
  on the `week15` branch (cut from `main` HEAD `7cc2921` on
  `2026-05-14`); see
  `documents/active-work/W15-codex-uclass-bounds-posture.md`. W15-1
  closed `2026-05-14` via `c58c365` (sync analyze error taxonomy parity,
  M10 close); W15-2 closed `2026-05-14` via `765cde7` (`clean_workspace`
  is_symlink-before-rmtree, M12 close); W15-3 closed `2026-05-15` via
  `3512a7c` (`activationEvents` bounds + Alembic field-length migration,
  U8 close); W15-4 closed `2026-05-16` via `89e13e3` (UI bounds bundle:
  `EventTimeline` / `EventDensityStrip` / `InteractionsSection` caps
  with truncation indicators, U1/U2/U3 + U6 close); **W15-1 post-slate
  typing hotfix** landed `2026-05-16` via `976dc96`
  (`ANALYZE_*_ERROR_TYPES` annotation `tuple[type[BaseException], …]`
  → `tuple[type[Exception], …]` narrowing surfaced by W15-4 close-out
  mypy gate; W14-7 hotfix precedent). W15-5..W15-7 pending sequential
  pull. **W15 mid-iter hygiene `2026-05-16`:** W15-7 doc-preamble
  subset pulled forward; six canonical doc preambles refreshed to W15
  truth-state and `tests/architecture/test_doc_preamble_consistency.py`
  added; three new audit findings appended to `POST_POC_BACKLOG.md` —
  `[FOLLOWUP health-reconciliation-responsibility-split]`,
  `[CLEANUP marketplace-router-test-suite-split]`,
  `[FOLLOWUP analysis-job-worker-entry-crud-ownership]`. Remaining
  W15-7 items (compose image pin + GH-action pin) still pending. Past
  trackers are stable-ID references only: W14, W13, W12, W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
