# W23 — reliability-self-defense (v1.0 trust floor, Stream 1)

`Last Updated: 2026-06-08`

`Branch: week23 (single branch — all Stream 1 development lands here; no per-item feature branches). Based on main @ c4b4eff.`

`Owner: ekrem`

`Status: IN PROGRESS — S1 + S3 landed; S2 (gated, alembic) and S4 (UI) pending. S5 non-blocking. Close-out (S6) is a gated PR.`

> Scope locked to **tight Stream 1** (per the 2026-06-08 planning session):
> reliability/self-defense only. The broader "Week24 trust floor" addendum
> items W24-6 (ADR-0015 E1/E2 evasion) and W24-7 (`vsix_sha256` provenance)
> are **out of scope** here — deferred to Streams 3/6. Canonical plan:
> [`v1-roadmap.md`](v1-roadmap.md) §5. Stable IDs: `POST_POC_BACKLOG.md`
> "Newly Captured (v1.0 roadmap intake 2026-06-08)".

## Goal

Close v1.0 bar **B1** (un-hangable by its own input), **B3** (never silently
wedges), **B4** (INCONCLUSIVE can never read as CLEAN), plus the low-severity
self-defense fixes F-2 / F-3. Reliability before measurement: this stream
precedes any catch-rate/provenance work.

## Sub-item status

| Sub-item | Closes | Status | Commit / note |
|---|---|---|---|
| **S0** doc-reconcile + active-stream pointer flip | — | partial | tracker (this file) + backlog/roadmap updated; **active-stream pointer flip (`phase.json` / `CLAUDE.md` / `REFACTOR_STATUS.md` header) is GATED — held for explicit go-ahead** |
| **S1** kill F-1 PEM ReDoS at source | B1 | ✅ done | `729d0d3` — `redact_secrets` routes private_key through a linear marker-pairing scanner (`_redact_private_key_spans`, no span cap); report-path timing + oversize-span regressions; direct `redact_secrets` ReDoS + semantics unit tests |
| **S2** heartbeat + reaper + terminal-write guard | B3 | ⏳ pending | **GATED** — adds nullable `last_heartbeat_at` (alembic migration needs explicit go-ahead before creation/run) |
| **S3 / F-2** offline `.vsix` pre-read size gate | — | ✅ done | `e3a8af6` — pre-read `st_size` gate on the operator-tuned `vsix_max_uncompressed_size` (no new knob); ingest → structured 422, list → skip; router resolves the threshold; integration + direct unit regressions |
| **S3 / F-3** import-graph relative-import resolution | — | ✅ done | `818c6be` — `_resolve_relative_import` in `boundaries.py` + `executor.py` + `facades.py` (roadmap-named `facades.py:38` copy was **dead/unused**; real gate is the other two); resolver fixture test; no real violation surfaced (relative imports cannot cross a top-level boundary — completeness fix) |
| **S4** stop false-clean UI tone | B4 | ⏳ pending | wire the 5-state `verdictColors.ts` palette into report/simulation surfaces; INCONCLUSIVE = non-green STOP; snapshot tests |
| **S5** ext-host ReDoS sweep (audit) | — | ⏳ pending | **non-blocking** — document the parse/marker regex family as line-anchored/linear; close the standing "unaudited" flag |
| **S6** close-out PR | — | ⏳ pending | **GATED** — PR only on explicit go-ahead; all pre-close findings resolved/waived first |

## Pre-close checklist (fresh audit findings, 2026-06-08)

Bucketed, evidence-cited, blocking flags noted. Mirrors `v1-roadmap.md` §6.

| Finding | Severity | Disposition |
|---|---|---|
| F-1 unbounded PEM redact on ext-host window | Medium | **RESOLVED** — S1 `729d0d3` |
| F-2 unbounded offline `.vsix` read | Low | **RESOLVED** — S3 `e3a8af6` |
| F-3 import-graph gate skips relative imports | Low | **RESOLVED** — S3 `818c6be` |
| `[BUG verdict-color-inconclusive-renders-clean]` | High (safety) | **OPEN** — S4 (blocking) |
| `[BUG wedged-job-no-same-boot-recovery]` | High (operability) | **OPEN** — S2 (blocking) |
| ext-host log-parse / strace ReDoS sweep | uncharacterized | **OPEN** — S5 (non-blocking; audit reclassified linear) |

## Verification (as of this update)

- S1: 78 redaction tests + 4 new direct `redact_secrets` tests green; adversarial
  200-unmatched-BEGIN payload ~6 ms (was ~360 ms). ruff/format/mypy/bandit clean.
- S3: 265 marketplace tests + 332 architecture tests green; F-3 surfaced **no real
  import-boundary violation**. ruff/format/mypy/bandit/markdownlint clean.
- All commits passed the full pre-commit hook chain.

## Operational notes

- **Source is baked into `automation_api`** — a live re-scan exercises these fixes
  only after `docker compose build api && up -d api`. S1 was verified live on a
  `dbaeumer.vscode-eslint@3.0.29` scan (job `completed`, verdict `clean`, report
  bundle 200 OK, no errors).
- **S2 alembic gotcha:** after the heartbeat column lands, `alembic-upgrade extrace`
  (5432) or `make check-all` fails `UndefinedColumn` until the dev DB is migrated.
- Regression surface to watch: CRSC-2 / W13-7 (redaction hardening S1 completes);
  the analyze error taxonomy (S2's guard must not break the closed-taxonomy →
  HTTP-map contract); ADR 0010 (observability — heartbeat is `run_id`-adjacent).
