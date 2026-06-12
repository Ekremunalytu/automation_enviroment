# ExTrace v1.0 Roadmap — From Finished Prototype To A Tool An Analyst Trusts Daily

`Last Updated: 2026-06-12`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: reliability-self-defense (v1.0 trust floor, Stream 1) — in progress on the week23 branch; closes v1.0 bars B1/B3/B4 plus self-defense fixes F-2/F-3. Tracker: documents/active-work/W23-reliability-self-defense.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

`Phase: PLANNING state — forward roadmap after podman-airgapped-deploy. Not yet the active stream; the first stream (reliability-self-defense) is opened only on explicit user go-ahead.`

`Owner: ekrem`

> **Authored 2026-06-08.** Direction set by the user after the project report
> was delivered: continue ExTrace as a **real, daily-usable, single-operator
> defensive tool** (not a demo, not research-only, not a handoff). Built via two
> multi-agent passes — a strategic-fork bake-off (health / security / detection /
> field-readiness, judged on mission/feasibility/leverage) then a 7-dimension
> real-tool gap assessment + single-maintainer prioritization + synthesis. Every
> load-bearing claim below was verified against `main` @ `441cb72`.

This is the canonical planning tracker for the v1.0 arc. It supersedes the
completed `W18-W22-roadmap.md` window. Streams land in the post-W22 **named
stream** convention (branch + active-work tracker + ADR(s) + close-out PR), not
the weekly W-pointer cadence.

---

## 1. Goal

Turn a finished-grade prototype into a tool a security analyst trusts on the
**first malicious extension they feed it**. The gap is not breadth
(`coverage_summary.missing_capabilities == []` already) — it is **trust,
survival, and honesty** of a single verdict on a single extension.

## 2. Where ExTrace Stands (2026-06-08)

Impressive, finished-grade prototype — three-layer detection (s1-s20 static +
Semgrep advisory + A1-A8 dynamic), a real Playwright-driven sandbox, a 6-tab
console, ~2100 tests, 16 ADRs, 63 invariant gates, a real air-gapped Podman
deploy. But **not yet trustworthy per-run.** Three concentrated, verified gaps
separate "impressive prototype" from "tool an analyst trusts daily":

1. **The verdict is not trustworthy per-run** — catch-rate is _asserted_ against
   the 7 A-series synthetic canaries plus the demo runnable canary, not
   _measured_; the `run_quality` anchor flickers `degraded`/`inconclusive` on
   identical inputs; no `vsix_sha256` binds a report to the bytes scanned (no
   hash column on `analysis_job.py` / `extension.py`).
2. **The tool can be hung or fooled by its own input** — F-1 ReDoS is live on the
   verdict-producing path (`executor/flows/playwright/report_builder.py:292/294`
   → unbounded `private_key` regex at `evidence.py:56`; the bounded scanner
   exists but is unreachable from `redact_secrets`); a failed/evaded run renders
   **green** because the correct 5-state `ui/src/features/reports/verdictColors.ts`
   palette is dead code.
3. **It does not survive a normal workday** — the 2nd analyze on one long-lived
   appliance container deterministically fails at `reset_sandbox`
   (`reload_vscode.py` has no retry, single `return 1`); a wedged worker needs an
   API restart to recover (no heartbeat column).

None are breadth problems. All are concentrated, verified, mostly-small fixes.

## 3. The v1.0 Bar (north star — 10 checkable conditions)

Test for each: _does its absence let an analyst be wrong, hung, or fooled while
believing the tool is fine?_ B1-B7 are the **trust core** (unanimous across the
three prioritization judges); B8-B10 are the **credibility/operability floor**.

| # | v1.0 condition | Checkable acceptance |
|---|---|---|
| **B1** | Un-hangable by its own input | No adversarial extension output (200+ unmatched `BEGIN` markers in a 500-line window) stalls report build; F-1 closed at source; regression test targets `redact_secrets` via the report path. |
| **B2** | Survives back-to-back use | 2nd/3rd analyze on the _same_ long-lived container reach `install_extension`; lifecycle-harness test asserts it with no container restart. |
| **B3** | Never silently wedges | A hung/out-of-taxonomy-crashing worker auto-recovers and releases the single-active queue _without_ an API restart (heartbeat + stale-running reaper + terminal-write guard). |
| **B4** | INCONCLUSIVE can never read as CLEAN | All 5 verdict states colored distinctly; inconclusive is a non-green STOP; snapshot test asserts inconclusive/clean_with_notes never render the clean tone; legend + recommended-action present. |
| **B5** | Verdict bound to the bytes | `vsix_sha256` computed at intake, persisted on `AnalysisJob`, stamped into the report; two byte-different same-version VSIX are not conflated. |
| **B6** | Verdict reproducible | Same VSIX run twice → same malicious/clean/inconclusive verdict; `run_quality_reasons` partitioned into behavioral vs harness-health; residual variance is a labeled band, not silent flicker; N-run determinism test on the reference target. |
| **B7** | Structural blind spots can't read CLEAN | (a) OS-gated (win32/darwin) family on the Linux sandbox surfaces "dynamic platform-blind", not a clean dynamic pass; (b) ADR-0015 E1/E2 evasion _detection_ recorders route probe-then-dormant to inconclusive/suspicious. |
| **B8** | Catch-rate measured, not asserted | A small multi-variant labeled corpus (beyond the 7 A-series canaries plus the demo runnable canary) + the real benign extensions run end-to-end emit aggregate caught/missed/FP per family; a benign-FP gating scan asserts an explicit FP budget. |
| **B9** | Verdict can leave the tool | One backend endpoint returns a self-contained verdict+findings+mitigations+evidence artifact (JSON now, printable HTML next), downloadable offline with `Content-Disposition`; Export button on ReportsPage. |
| **B10** | Honest install & identity | `/api/health` probes DB (`SELECT 1`) + api container healthcheck; one coherent version source, git-tagged, stamped into every report; `extrace-ctl.sh backup`/`restore` so scan history survives an upgrade mistake. |

**v1.0 = B1-B10 closed (Streams 1-6). B8-B10 are gated AFTER the trust core**
because measuring/scaling on a flickering, un-provable verdict manufactures false
confidence.

## 4. Phased Roadmap — Named Streams

Sequenced by **dependency + de-risking**: reliability and reproducibility BEFORE
measurement; validation corpus BEFORE any catch-rate claim; sandbox-reuse BEFORE
batch.

| # | Stream | Theme | Closes | v1.0? |
|---|---|---|---|---|
| **1** | `reliability-self-defense` | Un-hangable, un-wedgeable, never silently false-clean | B1, B3, B4 (+ F-2/F-3) | yes |
| **2** | `reliability-multi-analyze` | Same appliance survives analyze #2, #3 on one container | B2 | yes |
| **3** | `verdict-provenance-reproducibility` (spine) | Same VSIX twice → same verdict; verdict bound to bytes | B5, B6 | yes |
| **4** | `operator-report-export` | Verdict can leave the tool as an actionable artifact | B9 | yes |
| **5** | `release-identity-ops` | Know the build, trust the green light, never lose history | B10 | yes |
| **6** | `measured-catch-rate` (mission core) | Detection asserted → measured; blind spots can't read CLEAN | B7, B8 | yes |
| **7** | `sequential-batch-corpus` | Point at a set, walk away, results table | — | post-v1.0 |
| **8** | `linux-host-hardening-evasion` | Shrink executor blast radius (Fedora-unblocked); extend evasion | — | post-v1.0 |

**Spine decision:** Stream 3 (reproducibility/provenance) precedes Stream 6
(measurement) — four downstream streams depend on a non-flickering, build-
attributable anchor. Getting that order wrong is the one mistake that lets the
project measure, calibrate, and scale on sand.

## 5. First Stream In Detail — `reliability-self-defense`

Start point. Pure-reliability, mostly S/M, zero dependency, highest blast-radius.
Branch `feat/reliability-self-defense`, tracker
`documents/active-work/reliability-self-defense.md` (created at stream open).

| Sub-item | Files | Acceptance |
|---|---|---|
| **S0** doc-reconcile | new tracker + `CLAUDE.md` / `phase.json` active-stream pointer flip | stream registered as the named successor to `podman-airgapped-deploy`; audit findings recorded as the pre-close checklist (§6 below). |
| **S1** kill F-1 at source `[BUG report-builder-unbounded-pem-redact]` | `packages/analysis_contracts/evidence.py:56-62,84-91`; verify `executor/flows/playwright/report_builder.py:292/294` now bounded transitively | replace the lazy `(?:.\|\n)*?` `private_key` pattern in `_REDACTION_PATTERNS` so `redact_secrets` itself is bounded (route through `_redact_private_key_bounded`); new regression test asserts `redact_secrets` stays under a time ceiling on the 200-unmatched-`BEGIN` payload **via the report-build path**. |
| **S2** heartbeat + reaper + terminal-write guard `[BUG wedged-job-no-same-boot-recovery]` | `workflows/marketplace/analysis_execution.py:122`; `analysis_service.py:600/607`; `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`; alembic (heartbeat column) | heartbeat tick writes `last_heartbeat_at`; stale-running reaper releases the single-active lock **same-boot**; narrow boundary guard in `run_analysis_job` writes `fail_job` then **re-raises** (no bare except; new stage exceptions join `ANALYZE_ERROR_TYPES` + HTTP map + routing test). |
| **S3** F-2 + F-3 `[FOLLOWUP offline-vsix-size-bound]` + `[BUG import-graph-relative-import-gate-gap]` (done on `week23`) | `workflows/marketplace/offline.py` (pre-read gate) + `router.py` (resolve operator threshold); F-3 real gate is `tests/architecture/test_import_graph_boundaries.py` + `test_import_graph_executor.py` — the roadmap-named `test_import_graph_facades.py:38` copy was **dead/unused**; all three `_import_references` copies fixed | pre-read `st_size` cap (reuse the `vsix_max_uncompressed_size` family — no new knob) → clean 422 `vsix_threshold_breach` before `read_bytes()`; `_resolve_relative_import` resolves `node.level` to the absolute module instead of `continue`. Relative imports cannot cross a top-level boundary, so no real violation surfaced — gate-completeness/honesty fix. |
| **S4** stop false-clean UI tone `[BUG verdict-color-inconclusive-renders-clean]` (done on `week23`) | `ui/src/features/reports/verdictColors.ts` (canonical v3 palette); `ui/src/features/reports/ReportsPage.tsx`; `ui/src/features/simulation/runHealth.ts` (extracted `automationHealthTone`) | `verdictColors.ts` rebuilt as the v3-native 5-state source of truth (`verdictTone`/`verdictAction`/`VERDICT_STYLES`/`VERDICT_LEGEND`, `CLEAN_TONE`); the header badge, score cell, and rationale chips tone through it; added a recommended-action note + compact verdict-scale legend. INCONCLUSIVE → `neutral` STOP, `clean_with_notes` → `accent`, only `clean` → `ok`. SimulationPage's run-health was already `inconclusive`→`neutral`; extracted to a named, unit-tested helper (`automationHealthTone`) so the property is regression-guarded. Unit tests pin the distinct-tone bijection + "inconclusive/clean_with_notes never render the clean tone"; render test asserts the INCONCLUSIVE badge + non-clean action + legend. `tsc`/`eslint`/boundary-lint clean; full UI suite 131 tests green. |
| **S5** ext-host ReDoS sweep `[FOLLOWUP exthost-logparse-redos-bounds-sweep]` (done on `week23`) | `executor/host.py:65`; `runtime_capture/extension_host_strace_parse.py`; `health/handshake.py:37`; `runtime_capture/extension_host_log_parse.py` | audited all four regex-bearing ext-host files: the family is line-anchored/linear (strace `^…$`-anchored; harness mask = literal prefix + `\S+`; harness marker per-line single greedy `.*`; log patterns per-line behind an `activ`/`register` pre-filter). The audit found one real edge — `_ACTIVATION_PATTERNS[4]` was the only unanchored greedy-prefix pattern (O(n²) on a colon-less mega-line) — and **fixed** it: bounded the prefix `{1,256}` (linear) + added a 16 KiB per-line cap. 1M-char line minutes→~32 ms; 6 regression tests (3 for the `log_parse` fix + 3 in `test_exthost_parse_redos_bounds.py` pinning the other three audited regexes as linear, so the family claim is test-backed); 845 executor tests green. Standing "unaudited" flag closed. **Non-blocking.** |
| **S6** close-out PR | tracker freeze, pre-close checklist resolution | all audit findings resolved/waived with evidence before merge. **PR only on explicit user go-ahead.** |

**Regression surface:** CRSC-2 / W13-7 (the redaction hardening this completes);
ADR 0010 (observability — heartbeat is a `run_id`/`attempt_id`-adjacent signal);
the analyze error taxonomy (S2's guard must not break the closed-taxonomy →
HTTP-map contract). After the alembic change, `alembic-upgrade extrace` (5432) or
`make check-all` fails `UndefinedColumn` (dev-DB gotcha).

### Week24 Roadmap Addendum — Security Trust Floor (Future Candidate)

**Status:** roadmap-only. Do **not** open a branch, change
`documents/phase.json`, flip the active stream, create
`documents/active-work/reliability-self-defense.md`, add an Alembic migration, or
touch runtime/UI/test code until the user explicitly starts this work. W22
remains the last merged weekly pointer; Week24 is a future named-stream candidate,
not an active weekly phase.

**Goal:** make ExTrace prove its own analysis trustworthiness before any screen,
report, API response, or export lets an operator interpret a run as clean. This
is the security trust floor that should precede measurement, MITRE presentation,
batching, or broader field-readiness work.

| Candidate item | Intended implementation shape | Future acceptance / test notes |
|---|---|---|
| **W24-1 false-clean semantics** | Wire the 5-state verdict model into every analyst-facing report/simulation surface instead of deriving tone through a clean-like low-severity fallback. `inconclusive` must read as a stop/retry/review state, not success. | UI tests cover `clean`, `clean_with_notes`, `suspicious`, `malicious`, and `inconclusive`; snapshots assert `inconclusive` and `clean_with_notes` never render the clean tone. |
| **W24-2 PEM/log/report self-defense** | Close the unbounded PEM redaction path at the shared redaction source, then audit report assembly and extension-host log parsing so extension-controlled text cannot hang report generation or leak raw secret-shaped material. | Security regressions exercise adversarial unmatched-`BEGIN` payloads through the report-build path; log parsing remains bounded by line/window caps and produces sanitized samples. |
| **W24-3 offline VSIX/input bounds** | Add a pre-read outer file-size gate for offline `.vsix` intake using the existing VSIX threshold family; avoid loading an over-limit archive into memory before rejecting it. | Offline list/ingest tests assert over-limit archives fail cleanly before `read_bytes()` and return the same operator-facing threshold semantics as extraction-time breaches. |
| **W24-4 import-graph relative gate** | Tighten architecture import checks so relative imports are resolved to their effective package target instead of being skipped by `ast.ImportFrom.level`. | Architecture tests include relative-import fixtures for allowed and forbidden targets; real violations are fixed at the import site, not waived in the gate. |
| **W24-5 same-boot wedged-job recovery** | Plan a heartbeat-backed active-job recovery path for workers that die or hang inside the same API boot. This is the only expected schema change in the future implementation: a nullable heartbeat timestamp on `analysis_jobs`, written through CRUD and consumed by a stale-running reaper. | Storage/workflow tests prove a stale same-boot active row moves to a terminal failed state, releases the single-active slot, preserves terminal-write guards, and does not use a broad catch-all exception. |
| **W24-6 ADR 0015 E1/E2 foundation** | Start only the first sandbox-evasion slice: `navigator.webdriver` probing and CDP probing. The target behavior is suppression where safe plus detection records that prevent probe-then-dormant samples from reading clean. E3-E5 stay later. | Synthetic canaries produce explicit evasion evidence and route the run to `suspicious` or `inconclusive`; `EXECUTOR_CDP_PORT` remains default-off and pinned by the existing CDP invariant. |
| **W24-7 provenance anchor** | Add the minimum report identity spine for future reproducibility: dynamic and static outputs should carry the analyzed VSIX SHA-256 alongside the existing producer/build fingerprint. | Contract tests accept legacy blank/default values but require new producer paths to emit canonical 64-char lowercase hashes; dynamic/static/bundle outputs agree for the same analyzed bytes. |

**Out of Week24:** measured catch-rate/corpus gates, MITRE/dashboard work,
sequential batch, report export, release backup/restore, full ADR 0015 E3-E5,
and Linux host hardening. Those remain later roadmap work because they either
depend on this trust floor or belong to post-v1.0 hardening.

**Suggested future close criteria:** when explicitly started, Week24 should close
only after docs record the active stream transition, the trust-floor items above
have targeted regressions, `make test-security` includes any new security tests,
and the final PR states whether DB schema changed. Until then, this section is a
planning addendum only.

## 6. Pre-Close Checklist — Fresh Audit Findings (2026-06-08)

Recorded so they are never lost; bucketed, evidence-cited, none-blocking flagged
(per the audit-findings → pre-close-checklist practice). Stable backlog IDs live
in `POST_POC_BACKLOG.md` "Newly Captured (v1.0 roadmap intake 2026-06-08)";
the detailed intake snapshot is archived at
`documents/archive/backlog/v1-roadmap-intake-2026-06-08.md`.

| Finding | Severity | Disposition | Evidence |
|---|---|---|---|
| F-1 unbounded PEM redact on ext-host window | Medium | Stream 1 / S1 — **RESOLVED** (week23 `729d0d3`: linear marker-pairing scanner) | `executor/flows/playwright/report_builder.py:292/294`, `evidence.py:56-62,84` |
| F-2 unbounded offline `.vsix` read | Low | Stream 1 / S3 — **RESOLVED** (week23 `e3a8af6`: pre-read `st_size` gate) | `offline.py:178/229` |
| F-3 import-graph gate skips relative imports | Low | Stream 1 / S3 — **RESOLVED** (week23: `_resolve_relative_import`) | real gate `test_import_graph_boundaries.py` + `test_import_graph_executor.py` (roadmap-named `test_import_graph_facades.py:38` copy was dead/unused) |
| `[BUG verdict-color-inconclusive-renders-clean]` | High (safety) | Stream 1 / S4 — **RESOLVED** (week23: canonical v3 verdict palette; INCONCLUSIVE → neutral STOP) | `verdictColors.ts`, `ReportsPage.tsx`, `simulation/runHealth.ts` |
| ext-host log-parse / strace ReDoS sweep | uncharacterized | Stream 1 / S5 — **RESOLVED** (week23: family line-anchored/linear; one unanchored greedy-prefix pattern bounded `{1,256}` + 16 KiB per-line cap; 1M-char line minutes→~32 ms) | `extension_host_log_parse.py`, `extension_host_strace_parse.py` |
| `[FOLLOWUP vsix-entry-log-sanitization]` (raw entry names in logs) | Med/High | **Stream 4** (alongside offline skip-reason UX, same files) | `client.py:269/319` |

## 7. Stream → Stable ID Map

- **Stream 1** — `[BUG report-builder-unbounded-pem-redact]`, `[BUG wedged-job-no-same-boot-recovery]`, `[FOLLOWUP offline-vsix-size-bound]`, `[BUG import-graph-relative-import-gate-gap]`, `[BUG verdict-color-inconclusive-renders-clean]`, `[FOLLOWUP exthost-logparse-redos-bounds-sweep]`.
- **Stream 2** — `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (existing).
- **Stream 3** — `[GOAL vsix-content-sha256-provenance]`, `[GOAL verdict-reproducibility-anchor]`.
- **Stream 4** — `[GOAL report-export-artifact]`, `[FOLLOWUP vsix-entry-log-sanitization]` (existing), offline skip-reason UX.
- **Stream 5** — `[CLEANUP version-identity-coherence]`, `[GOAL api-health-db-probe]`, `[GOAL podman-backup-restore]`.
- **Stream 6** — `[GOAL measured-catch-rate-corpus]`, `[GOAL benign-false-positive-gate]`, `[GOAL platform-blind-verdict-annotation]`, `[GOAL adr-0015-e1-e2-evasion-detection]`.
- **Stream 7** (post-v1.0) — `[GOAL sequential-batch-corpus]`.
- **Stream 8** (post-v1.0) — `[GOAL container-hardening-ratchet-down]` (ADR 0013 §Deferred; W22-6 deferred-to-user), `[GOAL adr-0015-e3-e5-evasion-detection]`, `[FOLLOWUP harness-secret-distribution-redesign]` (existing).

## 8. Non-Goals (scope honesty)

Staying "a real single-operator tool" means we will **NOT** build:

- No distributed systems / queues / workers (no Kafka/Redis/Celery, no parallel
  sandboxes, no k8s). Batch (Stream 7) = one in-process serial drain loop only.
- No multi-tenant / SaaS / team features (no accounts/RBAC/shared-workspaces).
  One operator, one appliance, loopback-default (ADR 0007/0011).
- No SIEM/CEF/STIX/syslog/webhook emitters — the self-contained export artifact
  (B9) is the integration bridge.
- No "real malware" corpus — v1 corpus stays strictly synthetic/declawed
  (ADR 0004 + detection-design SAFETY); multi-variant near-misses, not live
  samples.
- No full ADR-0015 E1-E5 _masking_ suite at v1 — detection recorders only
  (E1/E2 in v1, E3-E5 post-v1.0).
- Deferred-not-cut ergonomics (post-v1.0): triage/disposition state, report diff,
  preflight/doctor screen, scan CLI, folder/installed-extension intake,
  marketplace-`latest` resolution.
- No new dependencies, no DI/plugin frameworks, no microservices. 4-pillar
  modular monolith unchanged.

## 9. Biggest Risk

Shipping a tool that is **broad but not trustworthy** — declaring v1.0 on
detection breadth while the per-run verdict remains un-provable, un-reproducible,
and silently-false-clean. Breadth _looks_ finished; the trust defects are small
and invisible until an analyst gets burned (a malicious extension that hangs
report build, a re-published malicious update conflated with a clean one, a failed
run rendered green, a verdict that flips on re-run, an evasive sample read as
CLEAN). Trust, once lost, does not come back from more rules. The sequence
mitigates this structurally by refusing to measure or scale before the verdict is
trustworthy.

## 10. Open Questions (resolve before sequencing the later streams)

1. **Is the Fedora box physically in hand?** ~~Gates the _live_ acceptance of
   Stream 5 (backup/restore, health on the real host) and Stream 8 (container
   ratchet-down kernel/seccomp validation).~~ **RESOLVED-BY-DEFERRAL
   (`2026-06-12`, user direction):** the Fedora-host-dependent _live-validation_
   is deferred to `POST_POC_BACKLOG.md` → `[FOLLOWUP fedora-host-live-validation]`
   and no longer blocks. Stream 5 lands its code + dev/CI validation now (live
   on-host proof pending); Stream 8 stays post-v1.0. The macOS dev host lands the
   _code_; the live proof is tracked separately, not gating.
2. **Is there a labeled malicious/benign extension set to measure catch-rate?**
   Gates Stream 6. v1 needs only a small multi-variant synthetic/declawed set
   beyond the 8 canaries + the real benign extensions already in `extensions/`.

## 11. Source

Workflow synthesis `extrace-real-tool-roadmap` (7-dimension gap assessment + 3
prioritization judges + synthesis), 2026-06-08. All file/line claims verified
against `main` @ `441cb72`.
