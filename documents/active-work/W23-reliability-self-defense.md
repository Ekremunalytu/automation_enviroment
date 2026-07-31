# W23 — reliability-self-defense (v1.0 trust floor, Stream 1)

`Last Updated: 2026-07-29`

`Branch: week23 (single branch — all Stream 1 development landed here; no per-item feature branches). Based on main @ c4b4eff. MERGED to main via PR #35 (week23 -> main) 2026-06-12, merge commit 653d807; the week23 branch was deleted post-merge.`

`Owner: ekrem`

`Status: MERGED — closed via PR #35 (week23 -> main) 2026-06-12, merge commit 653d807. All sub-items S0-S7 landed (S6 = the close-out PR #35 itself, merged 653d807); v1.0 bars B1/B3/B4 + F-2/F-3 closed; migration c3f8a1d7e9b2 on main. Named stream — last_merged_weekly stays W22. phase.json.active_stream named reliability-self-defense while this stream was open and later returned to null after W26; the current pointer names static-analysis-measurement-foundation. Codex review 2026-06-12 dispositions in the pre-close checklist below; pre-existing ui-boundaries/SettingsPage-ESLint waived (not W23).`

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
| **S0** doc-reconcile + active-stream pointer flip | — | ✅ done | `2026-06-12` (`0158d46`; body truth-sync `80dc5fc`) — `phase.json` `active_stream` flipped `podman-airgapped-deploy` → `reliability-self-defense` (tracker → this file); the `Active stream:` banner refreshed across all canonical preamble docs (CLAUDE.md / AGENTS.md / AGENT_CONTEXT.md / REFACTOR_STATUS.md / REFACTOR_OPTIMIZATION.md / POST_POC_BACKLOG.md / documents/README.md / active-work/README.md / v1-roadmap.md / root README.md) + `Last Updated` bumped. `last_merged_weekly` stays W22 (W23 not yet merged). Doc-preamble parity/consistency/manifest gates green |
| **S1** kill F-1 PEM ReDoS at source | B1 | ✅ done | `729d0d3` — `redact_secrets` routes private_key through a linear marker-pairing scanner (`_redact_private_key_spans`, no span cap); report-path timing + oversize-span regressions; direct `redact_secrets` ReDoS + semantics unit tests |
| **S2** heartbeat + reaper + terminal-write guard | B3 | ✅ done | `2026-06-12` (`744b3e1` feat + `eb79f79` tests) — migration `c3f8a1d7e9b2` adds nullable `last_heartbeat_at` (additive, no index/data motion; applied to dev DB `extrace`). Closes the same-boot gap `recover_interrupted_jobs` misses (it only reaps a *different* boot). **(1) heartbeat:** dedicated DB heartbeat thread spans claim→terminal (`job_service.run_job_heartbeat` → `touch_analysis_job_heartbeat`, targeted `UPDATE … WHERE status='running'`), independent of the per-phase monitoring heartbeat so a slow reset/install is not mistaken for a hang. **(2) reaper:** `reap_stale_running_analysis_jobs` fails same-boot `running` rows where `now - COALESCE(last_heartbeat_at, started_at) > EXTRACE_STALE_JOB_TIMEOUT_S` (default 120s), re-locked + re-checked under `with_for_update` before `_interrupt_job` (error_code `stale_heartbeat_reaped`); cancelling/queued/other-boot left alone. Triggered three ways (user-chosen "both"): submit (before `reserve_job`), status poll (`GET /analyze/{id}`), and a background daemon (`start_stale_job_reaper`, gated by `EXTRACE_SKIP_STALE_REAPER`, started in `create_app`). **(3) terminal-write guard:** `run_analysis_job` boundary `except Exception` writes a terminal state (cancel-aware) then re-raises — the AGENTS-rule-6 `[FOLLOWUP analysis-thread-supervisor]` landing site (`# arch-allow: thread-supervisor`) — so an out-of-taxonomy crash releases the slot immediately instead of wedging. No new pydantic contract (operational-only column). Tunables `EXTRACE_{HEARTBEAT_INTERVAL,STALE_JOB_TIMEOUT,REAPER_SWEEP_INTERVAL}_S` + `EXTRACE_SKIP_STALE_REAPER` documented in `.env.example`. |
| **S3 / F-2** offline `.vsix` pre-read size gate | — | ✅ done | `e3a8af6` — pre-read `st_size` gate on the operator-tuned `vsix_max_uncompressed_size` (no new knob); ingest → structured 422, list → skip; router resolves the threshold; integration + direct unit regressions |
| **S3 / F-3** import-graph relative-import resolution | — | ✅ done | `818c6be` — `_resolve_relative_import` in `boundaries.py` + `executor.py` + `facades.py` (roadmap-named `facades.py:38` copy was **dead/unused**; real gate is the other two); resolver fixture test; no real violation surfaced (relative imports cannot cross a top-level boundary — completeness fix) |
| **S4** stop false-clean UI tone | B4 | ✅ done | `verdictColors.ts` rebuilt as the canonical v3-native 5-state verdict palette (`verdictTone`/`verdictAction`/`VERDICT_STYLES`/`VERDICT_LEGEND`); `ReportsPage.tsx` header badge + score cell + rationale chips now tone through it, with a recommended-action note + compact verdict-scale legend; INCONCLUSIVE → `neutral` (grey STOP), `clean_with_notes` → `accent`, only `clean` → `ok` (`CLEAN_TONE`). Run-health analogue extracted to `simulation/runHealth.ts` (`automationHealthTone`, was already inconclusive→neutral; now named + tested). Unit tests pin the 5-state distinct-tone bijection + "inconclusive/clean_with_notes never render the clean tone"; ReportsPage render test asserts the INCONCLUSIVE badge + non-clean action note + legend |
| **S5** ext-host ReDoS sweep (audit) | — | ✅ done | audited the four regex-bearing ext-host files (`executor/host.py`, `health/handshake.py`, `runtime_capture/extension_host_strace_parse.py` + `…_log_parse.py`). Family is **line-anchored/linear** — strace `_PROCESS_EVENT_RE` is `^…$`-anchored with single greedy `.*`/`.+`; `_HARNESS_SECRET_MASK_RE` is a long literal prefix + `\S+` over a bounded error string; `_HARNESS_MARKER_RE` is per-line single greedy `.*`; the log patterns are per-line behind an `"activ"/"register"` substring pre-filter. **One** residual edge found+fixed: `_ACTIVATION_PATTERNS[4]` was the only pattern leading with an *unanchored* greedy `[\w.\-]+` prefix (O(n²) on a colon-less mega-line) → bounded to `{1,256}` (linear) + added a `_MAX_PARSE_LINE_LEN` (16 KiB) per-line cap. Empirically a 1M-char adversarial line went from **minutes → ~32 ms**. The standing "unaudited" flag is closed |
| **S6** close-out PR | — | ✅ done | PR #35 (`week23 -> main`) merged `2026-06-12`, merge commit `653d807`; all pre-close findings resolved/waived first |
| **S7** real-world extension compat (ingest + dynamic-install) | B-real-input | ✅ done | two fixes so current-marketplace extensions (GitHub Copilot Chat 0.48.1 as the driver) survive the pipeline: (1) **catalog ingest** — `ExtensionContributesSchema.configuration` widened `dict` → `dict \| list` (`catalog.py` + ORM `contributes.py` type hint); VS Code allows `contributes.configuration` to be a single object **or** an array, Copilot ships the array, which previously raised a pydantic `dict_type` error and aborted the whole catalog write. (2) **dynamic sandbox** — `EXECUTOR_VSCODE_VERSION` pin bumped `1.116.0` → `1.120.0` (`docker-compose.yml` default + `.env.example` + `deploy/podman/build-bundle.sh` + `DEMO_SCENARIO.md` hint); Copilot Chat 0.48.1 declares `engines.vscode ^1.120.0`, so 1.116 refused to install it (`not compatible with VS Code '1.116.0'`). Verified end-to-end: Copilot Chat now parses, installs (`rc=0`), and scans (static → `warn`, 7 benign first-party findings; dynamic → completes, `inconclusive` as it needs GitHub auth to activate). Playwright e2e (sim-demo + eslint monitor run) confirmed the 1.116→1.120 jump did not break the UI-driving flows. Tests: schema + pipeline + CRUD list-form `configuration` regressions; no test hard-codes the version (only the sed-normalization pattern) |

## Pre-close checklist (fresh audit findings, 2026-06-08)

Bucketed, evidence-cited, blocking flags noted. Mirrors `v1-roadmap.md` §6.

| Finding | Severity | Disposition |
|---|---|---|
| F-1 unbounded PEM redact on ext-host window | Medium | **RESOLVED** — S1 `729d0d3` |
| F-2 unbounded offline `.vsix` read | Low | **RESOLVED** — S3 `e3a8af6` |
| F-3 import-graph gate skips relative imports | Low | **RESOLVED** — S3 `818c6be` |
| `[BUG verdict-color-inconclusive-renders-clean]` | High (safety) | **RESOLVED** — S4 |
| `[BUG wedged-job-no-same-boot-recovery]` | High (operability) | **RESOLVED** — S2 `2026-06-12` (heartbeat + same-boot stale-running reaper + terminal-write guard; pushed `744b3e1`/`eb79f79`) |
| ext-host log-parse / strace ReDoS sweep | uncharacterized | **RESOLVED** — S5 (audit: family line-anchored/linear; the one unanchored greedy-prefix pattern bounded `{1,256}` + per-line cap; 1M-char line minutes→~32 ms) |

## Pre-close checklist (Codex independent review, 2026-06-12)

External verification pass run by the user via Codex before close-out. Each
finding bucketed + evidence-cited; W23-caused vs pre-existing-on-main flagged
(audit-findings → pre-close-checklist practice).

| Finding | Source | Disposition |
|---|---|---|
| `ui-boundaries` red — `RulesPage.tsx:25` cross-feature import `../reports/ruleCatalog` | **pre-existing on `main`, NOT W23** | week23 never touched `RulesPage.tsx` or `reports/ruleCatalog.ts`; W23's own UI files (`reports/`, `simulation/`) add **no** boundary violation. `make check-all` is red on `main` for this same line. **Disposition: WAIVE for W23 close-out** (not a W23 regression) — the proper fix (move `ruleCatalog` to a shared module) is a separate change. |
| global UI ESLint red — `SettingsPage.tsx:472` | **pre-existing on `main`, NOT W23** | week23 never touched `SettingsPage.tsx`. **Disposition: WAIVE for W23 close-out** (track separately). |
| Close-out docs contradictory — `AGENT_CONTEXT.md:30`, `v1-roadmap.md:11`, `active-work/README.md:28` still said podman-active / stream-not-opened | **W23-caused** (preamble parity gates only scan the first 10 lines; these bodies were missed in the S0 flip) | **RESOLVED `2026-06-12`** — all three bodies now name `reliability-self-defense` active on `week23`. |
| W23 tracker still `IN PROGRESS` / `commit pending` / `S6 pending` | **W23-caused** (stale after the push) | **RESOLVED `2026-06-12`** — status flipped to READY FOR CLOSE-OUT; `commit pending` removed (commits pushed); the S6 close-out PR was the last gated step, now merged as PR #35 (`653d807`). |
| No PR; local branch ahead of `origin/week23` | expected gated state | the S6 close-out PR is the merge mechanism itself (gated on explicit go-ahead); the `chore` gitignore commit is pending push with the PR. **Not a defect.** |

Green (Codex): Python 2673 passed · security lane 326 · UI 131 · ruff/mypy/bandit/markdownlint + UI production build clean · alembic single head `c3f8a1d7e9b2` · no W23-caused functional blocker in the heartbeat/reaper/migration review.

## Verification (as of this update)

- S1: 78 redaction tests + 4 new direct `redact_secrets` tests green; adversarial
  200-unmatched-BEGIN payload ~6 ms (was ~360 ms). ruff/format/mypy/bandit clean.
- S2: full suite **2671 passed, 11 skipped, 13 deselected** (no failures) on the
  S2 branch state. New coverage: 7 CRUD lifecycle tests (heartbeat stamp +
  same-boot reaper: stale-reap, fresh-skip, started_at fallback, other-boot skip,
  cancelling skip), 8 reaper/heartbeat thread+wrapper tests
  (`test_stale_job_reaper.py`), 1 alembic round-trip (`c3f8a1d7e9b2`), 1
  terminal-write-guard reraise test, 2 `create_app` reaper-gate tests, 2 endpoint
  sweep tests. Updated the lifecycle `__all__` surface pin + the
  AGENTS-rule-6 no-bare-except gate (pragma) both green. ruff/format/mypy/bandit
  (`-c pyproject.toml`) clean on all changed files. Migration applied live to dev
  DB `extrace` (column present, nullable). **Live anchor** — UI-driven scan
  `af40dd9bd2f4` (`dbaeumer.vscode-eslint@3.0.29`, 2026-06-12, api rebuilt with
  S2): `completed`, no error; `last_heartbeat_at` populated with a **215s
  heartbeat span over a 218s run** (ticked across reset/install/monitor with no
  gap → the reaper would not false-fire a slow-but-healthy run); reaper did not
  fire (`error_code` None, not `stale_heartbeat_reaped`). Prior jobs all show
  `last_heartbeat_at = NULL` (pre-S2 code), so the populated value is itself the
  proof the deployed api carries S2.
- S3: 265 marketplace tests + 332 architecture tests green; F-3 surfaced **no real
  import-boundary violation**. ruff/format/mypy/bandit/markdownlint clean.
- S4: full UI suite green — 23 files / 131 tests (10 new `verdictColors` unit tests,
  1 new `ReportsPage` inconclusive-verdict render test, 3 new `automationHealthTone`
  unit tests). `tsc -b`, `eslint`, and the UI boundary lint all clean on the changed
  files. (Live browser verification via the `ui-dev` vite preview on :5173 is the
  remaining optional visual confirmation — colors derive from the pre-existing
  `BADGE_TONE` map, which is unchanged.)
- S5: 845 executor tests green. ReDoS-sweep regressions: 3 in
  `test_playwright_extension_host.py` (the `log_parse` fix — adversarial 1M-char
  line minutes→~0.4–32 ms) plus 3 in `test_exthost_parse_redos_bounds.py`
  pinning the other three audited regexes (harness secret mask, harness marker,
  strace process-event) as linear on a 1M-char near-miss line, so the whole
  family's "linear" claim is **test-backed, not doc-asserted**.
  ruff/format/mypy/bandit clean.
- S7: list-form `configuration` regressions green at all three layers —
  `test_schemas.py::test_extension_contributes_schema_configuration_as_list`
  (contract), `test_manifest_to_schema.py::test_create_extension_with_list_form_configuration`
  (hydration pipeline), `test_crud.py::test_create_extension_with_list_form_configuration`
  (JSONB round-trip). VS Code pin bump verified live: executor rebuilt at 1.120.0,
  Copilot Chat 0.48.1 install `rc=0`, full eslint monitor run completed (Playwright
  flows intact); `test_container_dockerfile.py` + `test_podman_airgapped_deploy.py`
  green after the build-bundle/compose edits. Backup image
  `automation_enviroment-executor:vscode-1.116-backup` retained for instant revert.
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
