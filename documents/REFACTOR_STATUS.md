# Refactor Status

`Last Updated: 2026-08-03 — W22 closed synthetically on week22 and merged to main via PR #31 week22 -> main 1399f82. W21 closed and merged via PR #30 week21 -> main 2026-05-28 via 5dc18aa. Prior close-outs: W20 PR #29 week20 -> main 64a3c3d · W19 PR #28 week19 -> main c879603 · W18 PR #26 week18 -> main 9874e79 · W17 PR #25 week17 -> main bff565d · W16 PR #23 week16 -> main 1b6d43f · W15 PR #22 week15 -> main 6161472 · W14 PR #21 week14 -> main 4e03c8d · W13 PR #20 week13 -> main 772deb3. Latest merged named stream: verdict-provenance-reproducibility (W26), PR #38 bfb2d2d. Active named stream: static-analysis-artifact-precision (SAP-0..SAP-6), tracker active-work/static-analysis-artifact-precision.md, stacked on the unmerged SMF head; SAP-0..SAP-4 are complete and SAP-5 is next. Containment safety remains the next product/release gate from active-work/v1-roadmap.md §4.`

Active status board for current closure state. **Slim canonical** — verbose
phase evidence is frozen under dated snapshots:

- latest full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-06-15.md`](archive/status/REFACTOR_STATUS_full_2026-06-15.md)
- previous full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-13.md`](archive/status/REFACTOR_STATUS_full_2026-05-13.md)
- older full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-11.md`](archive/status/REFACTOR_STATUS_full_2026-05-11.md)
- older W4-W8 snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md)

## Current State

`static-analysis-artifact-precision` is ACTIVE. It is an offline/static SAR-2
stream; it does not advance the W22 weekly pointer or displace the
containment-first product execution order. SAP-0 through SAP-4 are implemented
and locally validated; SAP-5 reachability and deduplication is next. The branch
is stacked on the committed/pushed but
unmerged SMF head; neither stream has received PR/merge authorization in this
successor activation.

All weekly phases **W0-W22 are CLOSED and merged**. Per-phase PR/SHA close facts
are in the `Last Updated:` banner above; full per-iter evidence is frozen in the
dated archive snapshots + the per-week `active-work/W*.md` trackers (the stable-ID
owners). Headline timeline:

- **W0-W7** — PoC stabilization; §10.7 acceptance bar 11/11 green, closed `2026-04-23`.
- **PR345 + W8-0** — target activation lifecycle PRs 1-5 + ADR 0006, closed `2026-04-27`.
- **W8** — security hardening (W8-1..W8-7 + W8-9), closed `2026-04-29` (W8-8 deferred under `[FOLLOWUP w8-8-manifest-emit-when-needed]`).
- **W9** PR #9 `d67944d` · **W10** PR #11 `25e4c16` · **W11** PR #14 `50ca69e` · **W12** PR #18 `33a0852` — package-mode invocation, contract hygiene, monitor/workflow/storage split, executor subpackaging.
- **W13** Test Expansion + Observability — PR #20 `772deb3`, closed `2026-05-13`.
- **W14** Codex M-class Acceptance + Observability — PR #21 `4e03c8d`, closed `2026-05-14`.
- **W15** Codex U-class Close-Out + UI Bounds + Posture — PR #22 `6161472`, closed `2026-05-17`.
- **W16** Carry-Over Closeout + Audit Findings + Production Regression — PR #23 `1b6d43f`, closed `2026-05-18`.
- **W17** Carry-Over Closeout + Lifecycle Harness + Hygiene Sweep — PR #25 `bff565d`, closed `2026-05-18`.
- **W18** Heartbeat Refactor (ADR 0012) — PR #26 `9874e79`, closed `2026-05-21`.
- **W19** Live-Run Kök Neden: Dropout + Harness Verification — PR #28 `c879603`, closed synthetically `2026-05-26`.
- **W20** Coverage Promotion Round 1 (easy: `scm` + `settings`) — PR #29 `64a3c3d`, closed `2026-05-27`.
- **W21** Coverage Promotion Round 2 (mid: `testing` / `comments` / `workspace_trust` + container hardening baseline) — PR #30 `5dc18aa`, closed `2026-05-28`.
- **W22** Coverage Promotion Round 3 (hard: `chat`) + sandbox-evasion ADR 0015 + attribution depth — PR #31 `1399f82`, closed `2026-05-28`.

The **W18-W22 multi-iter roadmap** (three problem hatları — executor muhasebe /
harness verification gap / coverage-matrix promotion — and three capability layers
A/B/C) is complete; source-of-truth
[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md). Per-phase plans:
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) §11 (W8-W13) · §12-§20 (W14-W22).

## Post-W22 Feature Streams

These landed on `main` **after** the W22 weekly close-out. They are named
feature streams, **not** weekly (`W<N>`) phases, so they do not advance the
`documents/phase.json` weekly pointer (which stays W22 / PR #31 / `1399f82`) —
the same convention the static stream followed.

- **Static Analysis Pre-Check stream (ES-0..ES-5)** — the ADR 0016
  pre-execution static gate: the hardened `automation_static_analyzer`
  container, in-house static rules + the Semgrep runner, and the block-and-warn
  decision that fronts the dynamic sandbox. **Closed (ES-0..ES-5 DONE) and
  merged via PR #33 (`70e4364`).** Lane:
  [`agent-lanes/static-analysis-pre-check.md`](agent-lanes/static-analysis-pre-check.md);
  stream tracker:
  [`active-work/static-analysis-pre-check-stream.md`](active-work/static-analysis-pre-check-stream.md).
- **`extension-trigger-matrix` stream — merged to main `2026-06-03`.** Three
  workstreams (frozen tracker:
  [`active-work/extension-trigger-matrix.md`](active-work/extension-trigger-matrix.md)):
  1. **Reports Rule matrix tab** — a static + dynamic rule-activation grid
     (fired / silent / error / not-run) with click-for-detail; one additive
     backend touch (`ReportBundle.static_report` folds the sibling static
     report onto the `/bundle` response). UI-led.
  2. **Activation Coverage Promotion (executor + planner)** — the harness now
     exercises ambient-only extensions (`onStartupFinished` / `*`) by
     synthesizing `onCommand` attempts from `contributes.commands`, run safely
     via reload-deferral + inter-command maintenance (terminal-kill +
     renderer-liveness) + a finalize-in-`finally` so activation is parsed even
     on interrupt. Live-validated against an `ms-python.python` scan
     (22 extensions activated, 24/24 `onCommand` verified,
     `command_palette_unavailable` 60 → 0).
  3. **Static Rule Expansion + Blacklist** — in-house static rules 6 → 10
     (`s4`–`s7`), Semgrep JS rules 4 → 8, a dynamic `a7` blacklisted-domain
     rule, and an operator-editable DB-backed `blacklist_domains` denylist
     (seed ∪ operator; Alembic `b3d9f1c2e7a4`). `s4` is HIGH but WARNs (not a
     promoted blocker — gate unchanged).
  Lanes reconciled at this close-out:
  [`ui.md`](agent-lanes/ui.md),
  [`executor-runtime.md`](agent-lanes/executor-runtime.md),
  [`static-analysis-pre-check.md`](agent-lanes/static-analysis-pre-check.md).
  Close-out test bar (`2026-06-03`): full suite **2457 passed, 9 skipped,
  13 deselected** (post-W22 baseline 2450 + **7 merge-gating tests** added at
  close-out: blacklist-CRUD rollback ×2, seed-file `OSError` fallback,
  `prime_blacklist_override` swallow + happy-path, the `b3d9f1c2e7a4`
  migration round-trip, and `close_all_terminals`);
  `tests/architecture/` **318 passed**.
- **`security-development` stream — merged to main via PR #34
  (`f1dde63`) on `2026-06-04`; branch deleted post-merge.** Custom detection-rule expansion driven
  by a series of real-world malware classes (general, behaviour-class rules — no
  sample literal in rule logic). In-house static production rules grew to **26
  (`s1`-`s20`** across multi-rule modules); dynamic production rules to **A1-A8**
  (`a5.workspace_file_tamper`, `a8.reverse_shell` added); the Semgrep JS rule set
  to 16 (advisory echoes); plus the IOC denylist, the `.less`/`.scss`/`.sass`
  content-scanner coverage fix, and the UI Rules-tab catalog (static + dynamic,
  s1-s20). New static surfaces span reverse-shell (`s10`, CRITICAL), download-
  cradle (`s11`, CRITICAL), invisible-unicode (`s12`), native-loader (`s13`),
  globalState dormancy (`s14`), path-traversal (`s15`), cross-extension-tamper
  (`s16`, CRITICAL), credential-exfil (`s17`), download-exec dropper (`s18`),
  stylesheet threats (`s19` trio, inline-JS CRITICAL), RMM-as-RAT abuse (`s20`),
  reserved-publisher spoof (`s1.reserved_publisher_spoof`), plus the
  webhook/crypto (`s8`/`s9`) exfil surfaces. Real, observed C2/relay hosts are on
  the shared `blacklist_domains` denylist (the snowshono Stage-3 relay + related-
  campaign hosts + the kagema Stage-2 `niggboo.com`); SHA-256 hashes stay
  reference-only; shared first-party fallback hosts (Google Calendar/Gmail) are
  intentionally excluded to avoid broad false positives, and a guard test pins
  the IOC-safety invariant. Per-class specs (apollyon / securezeron / kagema /
  GlassWorm / snyk-labs / nf3xn / ecm3401 / nextsecurity / snowshono) and the
  living status board:
  [`detection-design/README.md`](detection-design/README.md).
- **Reliability — analyze resilience (direct-to-main, `2026-06-24/25`).** Three
  reliability fixes from real appliance failures: same-container multi-analyze
  reset (`reset_state.py` terminate tree-reaping; root cause was a malformed
  `pgrep` missing its `--` separator, not stale DevTools; `4437d1e`),
  analyze-timeout in-container **SIGKILL escalation** (`host.py`), and **adaptive
  early-give-up** for non-responsive targets (`stimulus/passes.py`).
  Live-verified (copilot-chat re-run: 160s, no zombie). Tracker:
  [`active-work/reliability-analyze-resilience.md`](active-work/reliability-analyze-resilience.md).
- **`verdict-provenance-reproducibility` (Stream 3 / W26) — merged via PR #38
  (`bfb2d2d`) on `2026-07-27`.** B5 binds DB, static report, and dynamic report
  to the analyzed VSIX SHA-256; B6 freezes capture health before verdict
  derivation and partitions run-quality reasons. Final gates: `make check-all`
  2726 passed, 11 skipped, 13 deselected; `make test-security` 326 passed.
  Tracker:
  [`active-work/W26-verdict-provenance-reproducibility.md`](active-work/W26-verdict-provenance-reproducibility.md).

## W13 Status Summary

| Scope | Status |
|---|---|
| Acceptance bar | W13-1..W13-7 closed H3/H4/H5/H6/M1/M9 from the 2026-05-10 Codex Cloud audit. |
| §11.10 GOAL pulls | W13-8 benign silence fixture 3->5, W13-9 `.env` gitignore gate, and W13-10 singleton-lock recovery closed. |
| Close-gate pulls | W13-11 HMAC python secret target-install race, W13-12 fail-closed harness handshake, and W13-13 worker-start cancel-race CAS closed in-window. |
| Merge | PR #20 `week13 -> main` merged `2026-05-13` via `772deb3`; W13 tracker remains as the stable-ID evidence file. |

## Current Deferrals

- `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` — programmatic Alembic
  upgrade/downgrade test, **pulled to W16-6** (hygiene splits + fresh-DB
  fixture).
- `[FOLLOWUP analysis-jobs-race]` — **closed** by W14-4 on `2026-05-13`;
  `complete_analysis_job` + `fail_analysis_job` now acquire
  `with_for_update()` and gate against `_TERMINAL_JOB_STATUSES`.
- `[FOLLOWUP simulation-progress-cancel]` remaining subitems
  (`heartbeat-sandbox-reset-off-thread`, `dedupe-step-progress-schemas`,
  `heartbeat-refactor`) — **W16-5 documented `2026-05-18` (scope
  reduced; no code commit)**: `dedupe-step-progress-schemas`
  **rejected** (distinct surface roles between strict storage variant
  and lenient public/UI variant; aliasing would couple them);
  `heartbeat-sandbox-reset-off-thread` + `heartbeat-refactor`
  **deferred to W17+** (lifecycle harness prerequisite).
- `[BUG scenario-dropout-upstream-root-cause]` — **closed** by W14-1 on
  `2026-05-13` via `0c8bd02` (deterministic repro matrix landed + conservation
  guard; severity downgraded BLOCKER -> HIGH same day; upstream emit-site
  split **pulled to W16-1** under `[FOLLOWUP scenario-accountant-conservation-split]`).
- `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — W15 mid-iter audit
  finding, **closed at W16-2** via `9d6d110` (row-lock-aware lifecycle CRUD
  primitive `claim_queued_analysis_job_at_worker_entry` extracted; W13-13
  CAS preserved; AGENTS.md:57 compliance restored).
- `[FOLLOWUP health-reconciliation-responsibility-split]` — W15 mid-iter
  audit finding, **closed at W16-4** via `304b99f` (responsibility-aligned
  three-way split: security.py + handshake.py + slimmed reconciliation.py;
  W13-1 HMAC + W13-12 fail-closed gates preserved). Pre-W16-4 description
  (behavior-preserving extraction with
  W13-1 HMAC gates preserved).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — W14 production
  scan-driven investigation, **null-leakage half closed at W16-3** via
  `fa430f2` (contract-seam additive fields + build_report_data populates;
  attribution-count-parity half split to a new follow-up). Pre-W16-3
  description (finalize ordering /
  `report.save()` drift).
- `[CLEANUP marketplace-router-test-suite-split]` + `[CLEANUP test-import-graph-policy-dump-split]`
  — **pulled to W16-6** (hygiene splits bundle).

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, keep closed W13 mechanics in
`active-work/W13-test-expansion-observability.md`, keep closed W14
mechanics in `active-work/W14-codex-acceptance-observability.md`,
keep closed W15 mechanics in
`active-work/W15-codex-uclass-bounds-posture.md`, keep closed W16
mechanics in `active-work/W16-regression-and-audit-closeout.md`,
keep closed W17 mechanics in
`active-work/W17-carryover-and-lifecycle-harness.md`, keep closed
W18 mechanics in `active-work/W18-heartbeat-refactor.md`, keep
closed W19 mechanics in
`active-work/W19-live-run-root-cause.md` (frozen at
W19-6-followup-2), and keep **closed W20 mechanics**
(coverage promotion round 1 easy wins; `scm` + `settings` official
promotion; W20-0..W20-5 sub-iter slate; merged via PR #29
`week20 -> main` / `64a3c3d`) in
`active-work/W20-coverage-promotion-easy-wins.md`, and keep **closed
W21 mechanics** in
`active-work/W21-coverage-promotion-mid-tier.md`. Multi-iter W18-W22
roadmap source-of-truth at `active-work/W18-W22-roadmap.md`
(W18-W22 closed and merged).
