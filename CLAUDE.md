# CLAUDE.md

`Last Updated: 2026-05-13 (W12 closed via PR #18; W13 — Test Expansion + Observability sub-iters W13-1..W13-10 closed; W13-11 HMAC python secret target-install race close-pass closed 2026-05-12 (Path A host-side eager-consume + env var passthrough, 6/6 main sub-commits + 7 post-landing additions in same push: 9a2ba76 self-stamp + doc fix-up + defense-in-depth b/c/a + README regex pin (steal-from-W13-13) + tracker test bar update; final bar test-local 1521 → 1537 / tests/architecture/ 105 → 112); W13-12 fail-closed harness handshake close-pass closed 2026-05-12 (5/5 sub-commits — docs lockdown + RED tests + impl + 3-fact arch gate + close sweep; `ActivationReport.harness_handshake_required: bool` on internal monitor dataclass + `_attempt_has_harness_completion_trace` fail-closed branch + `setup_monitor` stamps True; final bar test-local 1537 → 1539 (+2; 2 pre-existing env-only VSIX fixture failures unchanged) / tests/architecture/ 112 → 115 (+3)); W13-13 worker-start cancel-race CAS in-progress 2026-05-13 — Path B worker-entry `with_for_update()` snapshot design locked-in (sub-commit 1 docs lockdown landed; sub-commits 2-5 pending RED→impl→arch gate→close sweep); close-out PR week13 → main BLOCKED until W13-13 GREEN; W14 staging — Codex M-class Acceptance + Observability scoped into 6 sub-iter W14-1..W14-6, tracker documents/active-work/W14-codex-acceptance-observability.md, plan REFACTOR_OPTIMIZATION.md §12; W14 entry gate triggers after close-gate clearance + close-out merge)`

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
  W14 by section 12. W11 closed `2026-05-05` and merged via PR #14;
  W12 closed `2026-05-10` and merged into `main` via PR #18 (`33a0852`).
  **W13 — Test Expansion + Observability** (REFACTOR_OPTIMIZATION §11.10;
  tracker `documents/active-work/W13-test-expansion-observability.md`)
  closed sub-iters W13-1..W13-10 — acceptance bar (H3/H4/H5/H6/M1/M9) +
  §11.10 GOAL pulls (W13-8 benign silence fixture, W13-9 `.env` gitignore
  gate, W13-10 stale singleton-lock recovery test). **CLOSE-GATE HOLD
  `2026-05-11`** — Codex Cloud second-opinion review surfaced 3 P1
  close-pass items pulled as W13-11 (HMAC python secret target-install
  race — close-pass for W13-1 H6; **closed `2026-05-12`** 6/6
  sub-commits — Path A host-side eager-consume + env var passthrough),
  W13-12 (fail-closed harness handshake — close-pass for W13-1 H6,
  depends on W13-11; **closed `2026-05-12`** 5/5 sub-commits —
  `ActivationReport.harness_handshake_required: bool` + fail-closed
  branch + 3-fact AST gate), W13-13 (worker-start cancel-race CAS —
  close-pass for W13-3 H4; **in-progress `2026-05-13`** — Path B
  worker-entry `with_for_update()` snapshot design locked-in,
  sub-commit 1 docs lockdown landed, sub-commits 2-5 pending; original
  W13-13 scope included F4 README drift sweep +
  `tests/architecture/test_readme_phase_pointer.py` regex pin, both
  landed early in W13-11 push `2026-05-12` to keep the README sweep
  paired with its banner-cascade fix-up — W13-13 elde kalan iş =
  worker-entry CAS only). Close-out PR `week13 → main` BLOCKED until
  W13-13 GREEN. Items pulled in-window (not W14) to preserve
  audit-trail integrity for originally W13-claimed H6 + H4 closures.
  **Next phase: W14 — Codex M-class Acceptance + Observability** (staging;
  REFACTOR_OPTIMIZATION §12; tracker
  `documents/active-work/W14-codex-acceptance-observability.md`). Scope:
  6 sub-iter (W14-1 BLOCKER scenario-dropout araştırması, W14-2 input
  validation M4-M7+M11, W14-3 dış yüzey M13+M14b+U4-U12, W14-4
  correctness analysis-jobs-race + evidence-event-kind invariant,
  W14-5 logger consolidation + run-ID stamping + codex-automation-5
  fingerprint, W14-6 W8-W12 regression lock-in umbrella). Entry gate
  W13-13 close-gate clearance + close-out PR merge'de tetiklenir
  (W13-11 ve W13-12 zaten closed `2026-05-12`); stable ID'ler ilk
  pull'da atanır.
  Past trackers (stable-ID reference only):
  `documents/active-work/W12-executor-subpackaging.md`
  (W12-0..W12-5);
  `documents/active-work/W11-monitor-lifecycle.md`
  (W11-1..W11-8);
  `documents/active-work/W8-security.md` (closed `2026-04-29`).
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
