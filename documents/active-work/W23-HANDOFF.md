# W23 Handoff — reliability-self-defense (Stream 1)

`Created: 2026-06-09` · `Branch: week23` · `Base: main @ c4b4eff` · `Owner: ekrem`

> **Resume-cold doc.** Everything ungated in Stream 1 is **done, committed, and
> pushed**. What remains is **gated** (needs an explicit "go ahead" in-session):
> S2 (alembic migration), S0 (active-stream pointer flip), S6 (close-out PR).
> Canonical detail lives in
> [`W23-reliability-self-defense.md`](W23-reliability-self-defense.md) (stream
> tracker) and [`v1-roadmap.md`](v1-roadmap.md) §5/§6. This file is the short
> "pick up here" pointer.

## Git state (as of handoff)

- `week23` is **pushed and in sync** with `origin/week23` (0 ahead / 0 behind).
- 7 commits on top of `main @ c4b4eff`:

| Commit | What |
|---|---|
| `729d0d3` | **S1** — F-1 PEM ReDoS killed at source: `redact_secrets` routes `private_key` through a linear marker-pairing scanner (`_redact_private_key_spans`, no span cap). |
| `e3a8af6` | **S3/F-2** — offline `.vsix` pre-read `st_size` gate on the operator-tuned `vsix_max_uncompressed_size` (no new knob); ingest → structured 422, list → skip. |
| `818c6be` | **S3/F-3** — import-graph gate resolves relative imports (`_resolve_relative_import`); no real violation surfaced (completeness fix). |
| `7a0b5ce` | S1/S3 direct unit tests + the Stream 1 tracker. |
| `69328d1` | **S4** — false-clean verdict tone (B4): `verdictColors.ts` rebuilt as the canonical v3 5-state palette; INCONCLUSIVE → neutral STOP; legend + recommended-action; `automationHealthTone` extracted. |
| `6d175cb` | **S5** — ext-host log-parse ReDoS sweep: bounded the one unanchored greedy-prefix pattern `{1,256}` + 16 KiB per-line cap. |
| `566b398` | **S5** — ReDoS-linearity backstop tests for the other three audited regexes (family now test-backed). |

## Done (ungated) — all landed + verified live

- **S1 / F-1 / F-2 / F-3 / S4 / S5** complete. See the table above + the tracker.
- **Deployed to the running stack and verified by a live UI scan:**
  - **S4** → `ui` image rebuilt (`docker compose build ui && up -d ui`); served bundle carries the new palette (markers `Verdict scale`, `Recommended action`, `not a clean result`).
  - **S5** → `executor` image rebuilt; `_MAX_PARSE_LINE_LEN` + the `[\w.\-]{1,256}` bound confirmed baked into the running container.
  - Live `dbaeumer.vscode-eslint@3.0.29` scan after the rebuild: HTTP 200 bundle, all three sections, **verdict `clean`** (genuine — 0 findings / 9 rules fired), `run_quality=low` + `automation_health=degraded` (reason `skipped_scenarios_present`). The S5-touched parser produced **17 correct activation evidence events** with intact id/event/timestamp → activation parsing not regressed.
- **Tests green:** UI 131 (vitest), executor 848 (+ the S5 suites); `tsc -b` / `eslint` / UI boundary-lint clean; all commits passed the full pre-commit chain.

## Pending — ALL GATED (do not start without an explicit in-session "go ahead")

1. **S2 — heartbeat + reaper + terminal-write guard** (closes **B3**, last *blocking* item, High/operability).
   - Adds a **nullable `last_heartbeat_at`** to `analysis_jobs` → **alembic migration** (the gated step).
   - Heartbeat tick writes the column; a stale-running reaper releases the single-active lock **same-boot**; a narrow boundary guard in `run_analysis_job` writes `fail_job` then **re-raises** (no bare except).
   - **Contract rule:** any new stage exception must join `ANALYZE_ERROR_TYPES` + the HTTP map + a routing test (see memory: "analyze worker has no catch-all").
   - **Gotcha:** after the column lands, run `alembic-upgrade extrace` (dev DB on 5432) or `make check-all` fails `UndefinedColumn` (test DB on 5434 is `create_all`-managed, separate).
   - Files: `workflows/marketplace/analysis_execution.py`, `analysis_service.py`, `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`, alembic.

2. **S0 — active-stream pointer flip** (doc/infra).
   - Flip the active-stream pointer in `phase.json` / `CLAUDE.md` header / `documents/REFACTOR_STATUS.md` from `podman-airgapped-deploy` → the `reliability-self-defense` / `week23` stream.
   - Held deliberately for explicit go-ahead.

3. **S6 — close-out PR** (gated).
   - PR `week23 -> main` **only on explicit user go-ahead**; resolve/waive the pre-close checklist in the tracker first. Never open/merge/push a PR without an in-turn "go ahead".

## Operating rules to carry into the next session

- **Stop-and-ask before critical changes:** DB migrations, shared-contract mutations, infra/compose, feature-flag flips, deletes/overwrites, and **push / PR** — even mid-task after a general "continue". A general "devam et" does **not** authorize the gated items above.
- **Deploy correctly (do NOT `make rebuild`):** `make rebuild` = `docker-compose build --no-cache` on all 4 images in parallel → it OOM'd the ~7.75 GB Docker VM (host disk tight, ~16 GiB free). Instead build **only the changed service, cached**: `docker compose build <svc> && docker compose up -d <svc>`. Image→source map: UI changes → `ui` (nginx static, no HMR); ext-host runtime parsers → `executor`; host orchestration (`executor/host.py`) is baked into `api`.
- **Never read `.env`/secret files via shell** (PreToolUse hook blocks it; get values from `psql -l` / compose).
- **pre-commit is stricter than `make`** (mypy no `--ignore-missing-imports`; bandit default-level needs `# nosec`). Green `make check-all` ≠ commit passes.
- **Test invocation:** `.venv/bin/python -m pytest …`; UI → `npx vitest run` / `npx tsc -b` / `npx eslint` (real typecheck is `npm --prefix ui run build`, not root tsconfig).
- **Phantom-file caution:** re-read the exact region fresh before editing.

## Sources of truth (read path)

1. `documents/active-work/W23-reliability-self-defense.md` — Stream 1 tracker (S0–S6 status, pre-close checklist, verification, operational notes).
2. `documents/active-work/v1-roadmap.md` — §5 sub-item plan, §6 pre-close findings (F-1/F-2/F-3/S4/S5 all RESOLVED).
3. `documents/POST_POC_BACKLOG.md` — Stream 1 line + stable IDs.
4. `AGENTS.md` / `documents/AGENT_CONTEXT.md` — hard rules + task routing.

## First commands on resume

```bash
git checkout week23 && git pull --ff-only        # should be in sync
docker compose ps                                 # confirm stack up (6 services)
.venv/bin/python -m pytest tests/executor -q      # 848 green
( cd ui && npx vitest run )                        # 131 green
```

## FYI (not week23's doing)

GitHub Dependabot reports **5 vulnerabilities on the default branch** (2 critical,
2 high, 1 moderate) — these are dependency advisories on `main`, unrelated to the
week23 changes. A candidate for a separate task (review + bump PR), not part of
Stream 1.
