# W23 — reliability-self-defense (v1.0 trust floor, Stream 1)

`Last Updated: 2026-06-09`

`Branch: week23 (single branch — all Stream 1 development lands here; no per-item feature branches). Based on main @ c4b4eff.`

`Owner: ekrem`

`Status: IN PROGRESS — S1 + S3 + S4 + S5 + S7 landed; S2 (gated, alembic) pending. Close-out (S6) is a gated PR.`

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
| **S4** stop false-clean UI tone | B4 | ✅ done | `verdictColors.ts` rebuilt as the canonical v3-native 5-state verdict palette (`verdictTone`/`verdictAction`/`VERDICT_STYLES`/`VERDICT_LEGEND`); `ReportsPage.tsx` header badge + score cell + rationale chips now tone through it, with a recommended-action note + compact verdict-scale legend; INCONCLUSIVE → `neutral` (grey STOP), `clean_with_notes` → `accent`, only `clean` → `ok` (`CLEAN_TONE`). Run-health analogue extracted to `simulation/runHealth.ts` (`automationHealthTone`, was already inconclusive→neutral; now named + tested). Unit tests pin the 5-state distinct-tone bijection + "inconclusive/clean_with_notes never render the clean tone"; ReportsPage render test asserts the INCONCLUSIVE badge + non-clean action note + legend |
| **S5** ext-host ReDoS sweep (audit) | — | ✅ done | audited the four regex-bearing ext-host files (`executor/host.py`, `health/handshake.py`, `runtime_capture/extension_host_strace_parse.py` + `…_log_parse.py`). Family is **line-anchored/linear** — strace `_PROCESS_EVENT_RE` is `^…$`-anchored with single greedy `.*`/`.+`; `_HARNESS_SECRET_MASK_RE` is a long literal prefix + `\S+` over a bounded error string; `_HARNESS_MARKER_RE` is per-line single greedy `.*`; the log patterns are per-line behind an `"activ"/"register"` substring pre-filter. **One** residual edge found+fixed: `_ACTIVATION_PATTERNS[4]` was the only pattern leading with an *unanchored* greedy `[\w.\-]+` prefix (O(n²) on a colon-less mega-line) → bounded to `{1,256}` (linear) + added a `_MAX_PARSE_LINE_LEN` (16 KiB) per-line cap. Empirically a 1M-char adversarial line went from **minutes → ~32 ms**. The standing "unaudited" flag is closed |
| **S6** close-out PR | — | ⏳ pending | **GATED** — PR only on explicit go-ahead; all pre-close findings resolved/waived first |
| **S7** real-world extension compat (ingest + dynamic-install) | B-real-input | ✅ done | two fixes so current-marketplace extensions (GitHub Copilot Chat 0.48.1 as the driver) survive the pipeline: (1) **catalog ingest** — `ExtensionContributesSchema.configuration` widened `dict` → `dict \| list` (`catalog.py` + ORM `contributes.py` type hint); VS Code allows `contributes.configuration` to be a single object **or** an array, Copilot ships the array, which previously raised a pydantic `dict_type` error and aborted the whole catalog write. (2) **dynamic sandbox** — `EXECUTOR_VSCODE_VERSION` pin bumped `1.116.0` → `1.120.0` (`docker-compose.yml` default + `.env.example` + `deploy/podman/build-bundle.sh` + `DEMO_SCENARIO.md` hint); Copilot Chat 0.48.1 declares `engines.vscode ^1.120.0`, so 1.116 refused to install it (`not compatible with VS Code '1.116.0'`). Verified end-to-end: Copilot Chat now parses, installs (`rc=0`), and scans (static → `warn`, 7 benign first-party findings; dynamic → completes, `inconclusive` as it needs GitHub auth to activate). Playwright e2e (sim-demo + eslint monitor run) confirmed the 1.116→1.120 jump did not break the UI-driving flows. Tests: schema + pipeline + CRUD list-form `configuration` regressions; no test hard-codes the version (only the sed-normalization pattern) |

## Pre-close checklist (fresh audit findings, 2026-06-08)

Bucketed, evidence-cited, blocking flags noted. Mirrors `v1-roadmap.md` §6.

| Finding | Severity | Disposition |
|---|---|---|
| F-1 unbounded PEM redact on ext-host window | Medium | **RESOLVED** — S1 `729d0d3` |
| F-2 unbounded offline `.vsix` read | Low | **RESOLVED** — S3 `e3a8af6` |
| F-3 import-graph gate skips relative imports | Low | **RESOLVED** — S3 `818c6be` |
| `[BUG verdict-color-inconclusive-renders-clean]` | High (safety) | **RESOLVED** — S4 |
| `[BUG wedged-job-no-same-boot-recovery]` | High (operability) | **OPEN** — S2 (blocking) |
| ext-host log-parse / strace ReDoS sweep | uncharacterized | **RESOLVED** — S5 (audit: family line-anchored/linear; the one unanchored greedy-prefix pattern bounded `{1,256}` + per-line cap; 1M-char line minutes→~32 ms) |

## Verification (as of this update)

- S1: 78 redaction tests + 4 new direct `redact_secrets` tests green; adversarial
  200-unmatched-BEGIN payload ~6 ms (was ~360 ms). ruff/format/mypy/bandit clean.
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
