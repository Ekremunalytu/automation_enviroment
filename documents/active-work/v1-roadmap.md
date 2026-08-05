# ExTrace v1.0 Roadmap — From Finished Prototype To A Tool An Analyst Trusts Daily

`Last Updated: 2026-08-05`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active named stream: static-analysis-artifact-precision (SAP-0..SAP-6), limited to offline/static analysis; the SMF foundation plus SAP-0..SAP-4 baseline merged via PR #40, SAP-5 is complete and published on codex/static-analysis-artifact-precision but is not merged, and SAP-6 is next. Latest fully closed named stream: verdict-provenance-reproducibility (W26), PR #38 bfb2d2d. Containment safety remains the next product/release gate.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + optional active stream; null when none is open).`

`Phase: Stream 1 (reliability-self-defense) MERGED to main via PR #35 (week23 -> main, 653d807) 2026-06-12. operator-console-honesty MERGED via PR #36 (week24 -> main, 1e3fba6) 2026-06-23. Stream 2 (reliability-multi-analyze / B2) landed direct-to-main as reliability hardening (4437d1e + A/B fixes). Stream 3 (verdict-provenance-reproducibility, B5+B6, the spine) MERGED via PR #38 (week26 -> main, bfb2d2d) 2026-07-27. The 2026-07-27 strategy revision preserves frozen stream numbers as cross-reference IDs but supersedes their execution order: containment and measured detection now precede export/release operations.`

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

**v1.0 = B1-B10 closed plus the containment safety gate below.** B7/B8
measurement now precedes B9/B10 export/release operations: measurement on a
flickering verdict is false confidence, but packaging a product before proving
containment and detection contribution is equally unsafe.

## 4. Phased Roadmap — Named Streams

Sequenced by **dependency + de-risking**: reliability and reproducibility BEFORE
measurement; validation corpus BEFORE any catch-rate claim; sandbox-reuse BEFORE
batch.

| # | Stream | Theme | Closes | v1.0? |
|---|---|---|---|---|
| **1** | `reliability-self-defense` | Un-hangable, un-wedgeable, never silently false-clean | B1, B3, B4 (+ F-2/F-3) | yes |
| **★** | `operator-console-honesty` | Stop the console lying: dead/decorative Settings+System controls made honest | — (UI-only honesty) | non-bar |
| **2** | `reliability-multi-analyze` | Same appliance survives analyze #2, #3 on one container | B2 | yes |
| **3** | `verdict-provenance-reproducibility` (spine) | Same VSIX twice → same verdict; verdict bound to bytes | B5, B6 | yes |
| **4** | `operator-report-export` | Verdict can leave the tool as an actionable artifact | B9 | yes |
| **5** | `release-identity-ops` | Know the build, trust the green light, never lose history | B10 | yes |
| **6** | `measured-catch-rate` (mission core) | Detection asserted → measured; static/dynamic contribution separated; blind spots can't read CLEAN | B7, B8 | yes |
| **7** | `sequential-batch-corpus` | Point at a set, walk away, results table | — | post-v1.0 |
| **8** | `linux-host-hardening-evasion` | Shrink executor blast radius; disposable per-analysis sandbox; extend evasion | — | safety slice before v1.0 |
| **9** | `operator-settings-ops` | Server-persist settings; telemetry retention/purge; danger wipe/reset | — | post-v1.0 |
| **10** | `operator-disposition` | Operator marks benign-domain findings (raw vs adjusted; never deletes) | — | post-v1.0 |
| **11** | `network-egress-enforcement` (mitmproxy) | Fail-closed egress + decrypted HTTP(S) evidence | — | safety slice before v1.0 |

**Spine decision:** Stream 3 (reproducibility/provenance) precedes Stream 6
(measurement) — four downstream streams depend on a non-flickering, build-
attributable anchor. Getting that order wrong is the one mistake that lets the
project measure, calibrate, and scale on sand.

**Sequencing update (2026-06-15, user direction).** A non-bar
`operator-console-honesty` stream (★) is sequenced **first**; Streams 2-8 keep
their frozen numbers + bar→ID mappings and shift one week label. Streams 9-11 are
stable cross-reference IDs, not priority ranks.

### Execution-order revision (2026-07-27)

The earlier `W27 export → W28 release → W29 measurement` cadence is
**superseded**. ExTrace remains a hybrid analyzer, but the product strategy is
now **static-primary, dynamic-evidence**:

1. **Containment safety gate** — pull the safety slices of Streams 8 and 11
   forward: one disposable sandbox and sample-specific temporary volume per
   analysis, immutable image, internal-only network, controlled proxy/sinkhole,
   direct-egress fail-closed, and teardown after the run. A long-lived reusable
   container may remain an optimization, never the security boundary.
2. **Measured detection baseline (Stream 6 / B7+B8)** — run a labeled,
   multi-variant declawed corpus plus a materially larger benign set; report
   per-family recall, raw false-positive rate, inconclusive rate, runtime, and
   the incremental contribution of static-only, dynamic-only, and combined
   analysis.
3. **Static-primary + threat-directed dynamic (Stream 6 strategy slice)** —
   expand manifest/activation analysis, AST and interprocedural taint,
   obfuscation/loader/native/WASM coverage, dependency inventory, publisher
   provenance, and version-diff analysis. Static findings produce a bounded
   dynamic plan: targeted triggers, seeded secrets/C2, time acceleration, and
   platform-specific routing. Broad UI stimulus remains fallback evidence, not
   the default engine.
4. **Operator report export (Stream 4 / B9)** — export only after the product can
   state what was measured, what was contained, and which layer contributed.
5. **Release identity and operations (Stream 5 / B10)** — finish version,
   health, backup, and restore mechanics; then declare v1.0.

The detailed implementation roadmap for the measured/static-primary slice is
[`static-analysis-improvement-roadmap.md`](static-analysis-improvement-roadmap.md).
Its stable `SAR-0` through `SAR-7` packages refine Stream 6. Increment A is open
as `static-analysis-measurement-foundation` (`SMF-0`–`SMF-8`), an offline/static
stream that does not change the containment-first product execution order.

The numeric stream IDs remain frozen so ADRs, tests, and backlog references do
not churn. This section controls execution order. Product positioning is
deliberately bounded: ExTrace does not prove an extension is clean; it combines
static risk signals with behavior observed under controlled conditions into an
evidence-backed risk assessment.

### Live validation evidence — ESLint 3.0.34 (2026-07-27)

A post-merge appliance scan of `dbaeumer.vscode-eslint` `3.0.34` completed in
213 seconds without a job error. The staged VSIX, DB row, static report, and
dynamic report agreed on SHA-256
`ca708f1739dee184b858d8d04a61a4cbe7b621a13748bc63e859232b22cf700b`,
confirming the B5 provenance spine on a real marketplace flow.

The run also validates the revised roadmap order:

- **Static precision is not yet product-grade.** The gate warned on 7 medium
  findings across 5 rule families. Capability signals for `postinstall`,
  `child_process`, and raw networking merit review, but `s3` classified three
  PNG assets as native binaries and `s5` treated documentation/license HTTP
  links as suspicious endpoints. Measurement must separate true capability
  risk from source-context false positives.
- **Dynamic silence was not a clean bill of health.** The target activated and
  7 event attempts verified, with no target-owned network, file, or process
  event and no dynamic rule firing. However, `run_quality=low`,
  `automation_health=degraded`, and all 5 requested scenarios were skipped
  (2 represented through layered attempts; 3 had no matching attempt).
- **Honest aggregate:** `signal_summary=needs_review` with score 14. The
  layer-local dynamic `clean` verdict must never override low-quality execution
  or the static `warn` gate in operator-facing product language. The correct
  statement is “no malicious behavior observed under these conditions;
  review required,” not “extension proven clean.”

The JSON artifacts remain local under `output/` and are intentionally not
committed; this section records only the bounded, non-sensitive evidence needed
to drive containment, measurement, and static/dynamic aggregation work.

## 5. First Stream In Detail — `reliability-self-defense`

Start point. Pure-reliability, mostly S/M, zero dependency, highest blast-radius.
**Merged to main via PR #35 (`653d807`) `2026-06-12`** — developed on the existing
`week23` branch (the planned `feat/reliability-self-defense` branch was folded into it); tracker
`documents/active-work/W23-reliability-self-defense.md`.

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

**Status:** SUPERSEDED by W23 (`reliability-self-defense`, opened on `week23`
`2026-06-12`). The trust-floor items W24-1..W24-5 below shipped as W23 S4 / S1+S5 /
S3 / S3 / S2 respectively (see the W23 tracker) — so the original "do not open a
branch / flip the active stream / add an Alembic migration until the user starts"
gate is satisfied. W24-6 (ADR-0015 E1/E2 evasion) and W24-7 (`vsix_sha256`
provenance) were explicitly OUT of W23 scope and remain deferred to Streams 3/6.
W22 remains the last merged weekly pointer.

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

### Next-Stream Plan (2026-06-15) — supersedes the Week24 Addendum above

> **Authored 2026-06-15. Supersedes the "Week24 Roadmap Addendum" subsection
> above** (those trust-floor items shipped as W23 / Stream 1). It inserts a new
> **non-bar** honesty stream ahead of Stream 2 (user direction), shifts the week
> labels of Streams 2-8 (numbers + bar→ID mappings stay frozen), and adds mitmproxy
> as the post-v1.0 egress mechanism. Load-bearing implementation claims were
> re-verified against `main` @ `9471ffe`. **None open yet** — opening (branch, `phase.json`
> active-stream flip, canonical-preamble refresh, ADR creation) is a separate H0
> step gated on explicit go-ahead.

**Why an honesty stream first.** The console ships decorative/dead controls that
imply a backend effect with no consumer — an operator-trust defect. Verified on
`main @ 9471ffe`: Settings GENERAL/EXECUTOR/TELEMETRY write only `localStorage`;
only `SecuritySection` is backend-wired; DANGER actions are disabled with
"Persistence API unavailable"; `timeZone`/`density`/`operatorName` have no
consumer outside `SettingsPage`. `SystemPage` renders mock cards as `synced`/`live`
while its `isStub` marker is not rendered, and labels the API-only `/api/health`
result as the executor card. Backend `APISettings.HEALTH_STATUS="OK"` also
mismatches the UI's exact lowercase comparison.

#### ★ W24 — `operator-console-honesty` (UI-only; NO backend / DB / detection / executor)

| Sub-item | Files | Acceptance |
|---|---|---|
| **H0** doc-reconcile + week-shift | tracker + `phase.json` active-stream + this roadmap | UI/docs-only; no DB touch |
| **H1** honest Settings | `SettingsPage.tsx` | every consumer-less control (autoAnalyze, strictNet, retention, verboseLogs, retainArtifacts, buffer, operatorName, timeZone, density, **theme**) → `disabled` + "Not yet enforced"; **pool size removed** or "Single active · serial" read-only (Non-Goal §8: no parallel sandboxes); fix the intro copy; remove/condition the general Save/Discard footer (SecuritySection keeps its own) |
| **H2** honest System | `SystemPage.tsx` | render `isStub` on every mock card (status/metrics/logs → "mock / not measured"); rename the `executor` card → `API`, real executor "not measured"; **normalize health status case-insensitively**, test with the real `"OK"`; soften the "All systems operational" headline |
| **H4** close-out PR | tracker freeze | gated on explicit go-ahead |

**Stretch (non-blocking):** H3 real Dark/Light theme (palette → CSS-variable;
re-enables the theme control); H1b `timeZone`→timestamp render +
`density`→row-height.
**Close-out gate:** `make ui-types-check` (even though DTOs are unchanged) + UI
lint + boundary-lint + Settings/System/Rules UI tests; `git diff --check`;
markdownlint + markdown-link-check on changed docs; and the doc-preamble,
canonical-preamble, README-phase-pointer, and phase-manifest architecture tests
must all be green.

#### Additional streams added by this plan

- **Stream 9 `operator-settings-ops`** — server-persist the operator settings
  (extend the `operator_settings` key-value store: `value` nullable + `value_text`
  sibling + CHECK-exactly-one + Pydantic key registry; `OperatorSetting.value` is
  int-only today) + telemetry retention/purge + DANGER wipe/reset
  (**factory-reset is hard-blocked until B10 backup/restore exists**).
- **Stream 10 `operator-disposition`** — operator marks benign-domain findings
  "operator-allowed"; **never deletes a finding or verdict**; the FP report shows
  **two metrics** (raw detection result + disposition-adjusted result). Roadmap §8
  classes triage/disposition as post-v1.0 ergonomics; it must **not** touch the B8
  gate, which measures **raw** detection/FP only.
- **Stream 11 `network-egress-enforcement` (mitmproxy)** — its minimal
  fail-closed containment slice is promoted before v1.0; operator-managed
  allowlists and broader protocol ergonomics remain later work.

#### Stream 11 — `network-egress-enforcement`: promoted containment gate (ADR + spike gated)

Today network observation is **passive tshark/dumpcap only** (`binary_paths.py`,
ADR 0013); there is **no egress enforcement** — `executor.control` is a
method-delegation boundary, not a network filter, and the executor sits on the
default Docker bridge with direct outbound (no custom `networks:` /
`internal:true` in `docker-compose.yml`; `cap_add: NET_RAW` only, no `NET_ADMIN`).
A forward proxy alone does **not** enforce egress.

> **mitmproxy is chosen as the interception engine. Implementation does not start
> until an ADR + a small network spike finalize enforcement topology, CA lifecycle,
> protocol coverage, and fail-closed behavior. The ADR
> (`documents/adrs/00XX-mitmproxy-egress-interception.md`) stays `Proposed` until
> the spike concludes — never `Accepted` before.**

**ADR + spike must resolve:**

- **Enforcement topology** — _(a) explicit-proxy_ (move the executor to an
  `internal: true` network, dual-home mitmproxy, non-proxy traffic fail-closed —
  closest to today's flat-bridge + NET_RAW-only posture, aligned with ADR 0013
  minimal-capability; **preferred**) vs _(b) transparent-gateway_ (routing/firewall;
  `NET_ADMIN` confined to a **separate gateway container**, never the executor).
- **CA lifecycle** — private key only on the proxy volume; the executor gets only
  the public CA cert; never baked into repo/image; generated per-install. The
  later operator-managed CA lifecycle extends B10 backup/restore; the pre-v1
  safety gate may use an ephemeral per-run CA.
- **Protocol coverage / evidence states** — explicit states `intercepted` /
  `blocked` / `direct_bypass_attempt` / `tls_pinning_or_trust_failure` /
  `uninspectable_protocol`. **Absence of a decrypted body is never CLEAN evidence**
  (B7). Fail-closed is disaggregated: TLS pinning/trust failure → connection fails
  and is recorded; proxy-unsupported protocol → fail-closed blocked; direct bypass
  attempt → recorded via tshark/network telemetry.
- **tshark ↔ mitmproxy correlation** — tshark sees the executor netns (packets),
  mitmproxy sees proxy flows; define how DNS / UDP / QUIC / failed-SYN /
  proxy-upstream are disambiguated so there is no double-count or false evasion.
  tshark stays.
- **Podman / air-gapped parity** — the new proxy image enters `build-bundle.sh`, is
  managed by `extrace-ctl.sh`, digest/version-pinned, carried in the offline bundle.

**Spike success criteria (all must hold):** (1) executor cannot reach the internet
directly; (2) allowed HTTP/HTTPS works through the proxy; (3) a forbidden domain is
blocked; (4) a connection ignoring proxy env fails closed; (5) a TLS-pinned sample
is not falsely CLEAN; (6) traffic fails closed when the proxy stops; (7) identical
result under Docker Compose **and** Podman; (8) **no `NET_ADMIN` added to the
executor**.

The pre-v1 slice is a fixed, fail-closed policy and does **not** depend on Stream
9. Making the `strictNet` toggle and operator-managed `egress_allowlist` real
still depends on Stream 9 persistence and remains a later operational slice.

#### Corrected design decisions

- **Pool size** removed as a control (Non-Goal: no parallel sandboxes;
  single-active queue / B3).
- **Whitelist** split into Stream 10 `operator-disposition` (finding annotation,
  marks not deletes) + `egress_allowlist` (network policy, in Stream 11 mitmproxy).
  The naive "blacklist mirror" was unsafe: the operator override reaches only the
  dynamic `a7` rule, the static `s4` is seed-only in `domain_indicators.py`, and
  `_common.is_benign_domain` already suppresses findings — so an
  operator-editable list that fully deletes critical findings is a trust hole.
- **W25 / B2** is root-cause-first: `reset_executor_sandbox_state`
  in `executor/host.py` **already retries the reload once** (the
  `reload_vscode.py` script itself has no script-local retry); the real work is a detailed rc=1
  root-cause + a **real same-container repro** (the mock lifecycle harness cannot
  prove it alone), with a cleanup pass **only if state-accumulation is proven**. The
  rc=1 root cause (`[FOLLOWUP sandbox-reset-stale-state-multi-analyze]`) remains a
  hypothesis (DevTools-state vs CDP-readiness/race both open).
- **B9** export carries no operator identity (download-focused GET); operator
  name persistence belongs to Stream 9.
- **B10** stays exactly its original scope (health DB probe + version identity
  + backup/restore); retention/settings/danger stay in Stream 9.
- **B8** measures **raw** detection/FP only; disposition (Stream 10) is
  informational and post-v1.0. Its execution now precedes B9/B10.

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

### Fresh Audit Findings (`extrace-audit` 2026-06-15)

Second read-only `/extrace-audit` pass against `main` @ `9471ffe` (code identical at
`d3b20ea`). Verdict **Mostly healthy with risks** — no Critical/High, no hard-rule
violation, 16/16 ADRs aligned, all 18 guard-drift flags adjudicated benign. Full
detail + stable IDs in `POST_POC_BACKLOG.md` "Newly Captured (extrace-audit
2026-06-15)". None blocking; the redaction item is the highest-leverage fix.

| Finding | Severity | Disposition | Evidence |
|---|---|---|---|
| Redaction enforced per-field, not at a chokepoint — 3 ungated extension-controlled report sinks (`LogStreamEntry.message/activation_event`, `FileEvent.path/summary`, `ProcessEvent.command/cwd`); sibling network producer redacts the same class | Medium (F1/F2), Info (F3) | `[BUG report-field-redaction-completeness]` — small + isolated; can ride any stream close-out | `scenario_accountant.py:574-576`, `filesystem.py:108-120` (vs `network.py:109-110`), `extension_host_strace_parse.py:71,88,97`, serialize `report_builder.py:384,408-411`; no AST gate |
| Stale CDP terminate-needle no-ops on the CDP-off default boot (reliability, not exposure) | Low | `[BUG reset-cdp-needle-stale]` → **Stream 2 / B2** (same-container reset); overlap closed-regression vs W14-3 | `reset_state.py:32/63/179` vs `launch_vscode.sh:27,96-99` |
| Pragma-ratchet test docstring says baseline 6/3-files; enforced constants are 7/4-files (gate correct) | Info | `[CLEANUP pragma-ratchet-docstring]` — trivial doc fix | `tests/architecture/test_bare_binary_pragma_ratchet.py:20-33` vs `:51-58` |
| `EventAttemptRecord` lacks `validate_assignment` → `confirmation_source` set-sites skip the validator (benign: hardcoded valid literals) | Info | `[CLEANUP event-attempt-validate-assignment]` — hardening hygiene | `contracts.py:223` (vs `ContentSample`), set-sites `reconciliation.py:348,363` |
| Container-isolation runtime gates skip on non-Docker dev host (runtime cap/flat-mode verified at compose/AST level only) | N/A (coverage-env) | already covered by `[FOLLOWUP fedora-host-live-validation]` + Stream 8 `[GOAL container-hardening-ratchet-down]` | `test_container_entrypoint.py`, `test_compose_isolation_invariants.py` |

## 7. Stream → Stable ID Map

- **Stream 1** — `[BUG report-builder-unbounded-pem-redact]`, `[BUG wedged-job-no-same-boot-recovery]`, `[FOLLOWUP offline-vsix-size-bound]`, `[BUG import-graph-relative-import-gate-gap]`, `[BUG verdict-color-inconclusive-renders-clean]`, `[FOLLOWUP exthost-logparse-redos-bounds-sweep]`.
- **Stream 2** — `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (existing), `[BUG reset-cdp-needle-stale]` (audit 2026-06-15).
- **Stream 3** — `[GOAL vsix-content-sha256-provenance]`, `[GOAL verdict-reproducibility-anchor]`.
- **Stream 4** — `[GOAL report-export-artifact]`, `[FOLLOWUP vsix-entry-log-sanitization]` (existing), offline skip-reason UX.
- **Stream 5** — `[CLEANUP version-identity-coherence]`, `[GOAL api-health-db-probe]`, `[GOAL podman-backup-restore]`.
- **Stream 6** — `[GOAL measured-catch-rate-corpus]`, `[GOAL benign-false-positive-gate]`, `[GOAL platform-blind-verdict-annotation]`, `[GOAL adr-0015-e1-e2-evasion-detection]`, `[GOAL measured-layer-contribution]`, `[GOAL static-primary-threat-directed-dynamic]`; detailed packages: [`SAR-0`–`SAR-7`](static-analysis-improvement-roadmap.md); active Increment A tracker: [`SMF-0`–`SMF-8`](static-analysis-measurement-foundation.md).
- **Stream 7** (post-v1.0) — `[GOAL sequential-batch-corpus]`.
- **Stream 8** — `[GOAL per-analysis-disposable-sandbox]` (pre-v1 safety
  slice), `[GOAL container-hardening-ratchet-down]` (ADR 0013 §Deferred;
  kernel/seccomp live proof remains Fedora-gated), `[GOAL
  adr-0015-e3-e5-evasion-detection]`, `[FOLLOWUP
  harness-secret-distribution-redesign]` (existing).
- **★ operator-console-honesty** (sequenced first, non-bar) — `[CLEANUP settings-decorative-controls-honesty]`, `[CLEANUP system-mock-status-honesty]`, `[GOAL light-dark-theme]` (stretch; non-blocking).
- **Stream 9 operator-settings-ops** (post-v1.0) — `[GOAL operator-settings-server-persistence]`, `[GOAL telemetry-retention-purge]`, `[GOAL danger-zone-destructive-actions]`.
- **Stream 10 operator-disposition** (post-v1.0) — `[GOAL benign-domain-disposition]` (raw vs adjusted; never deletes; NOT in the B8 gate).
- **Stream 11 network-egress-enforcement** — `[GOAL
  mitmproxy-tls-interception]` + `[GOAL direct-egress-fail-closed]` (pre-v1
  safety slice; ADR + spike gated; ADR stays `Proposed`), `[GOAL
  egress-allowlist-enforcement]` (later operator-managed slice; depends on
  Stream 9).
- **Audit captures (extrace-audit 2026-06-15; non-stream)** — `[BUG report-field-redaction-completeness]` (CRSC-2; can ride any close-out), `[CLEANUP pragma-ratchet-docstring]`, `[CLEANUP event-attempt-validate-assignment]`. (`[BUG reset-cdp-needle-stale]` lives under Stream 2 above.)

## 8. Non-Goals (scope honesty)

Staying "a real single-operator tool" means we will **NOT** build:

- No distributed systems / queues / workers (no Kafka/Redis/Celery, no parallel
  sandboxes, no k8s). Batch (Stream 7) = one in-process serial drain loop only.
- No multi-tenant / SaaS / team features (no accounts/RBAC/shared-workspaces).
  One operator, one appliance, loopback-default (ADR 0007/0011).
- No SIEM/CEF/STIX/syslog/webhook emitters — the self-contained export artifact
  (B9) is the integration bridge.
- No live malware in the repository, developer workstation, or ordinary CI
  (ADR 0004 + detection-design SAFETY). v1 regression gates stay
  synthetic/declawed. A product-level detection claim additionally requires an
  externally managed, access-controlled validation corpus that runs only inside
  the disposable containment environment and never lands in source control.
- No full ADR-0015 E1-E5 _masking_ suite at v1 — detection recorders only
  (E1/E2 in v1, E3-E5 post-v1.0).
- Deferred-not-cut ergonomics (post-v1.0): triage/disposition state, report diff,
  preflight/doctor screen, scan CLI, folder/installed-extension intake,
  marketplace-`latest` resolution.
- No new dependencies, no DI/plugin frameworks, no microservices. 4-pillar
  modular monolith unchanged.

## 9. Biggest Risk

Shipping a tool that is **broad but not trustworthy** — a reproducible report is
still not a security product if the sandbox permits uncontrolled egress or the
detection claim is based only on hand-authored canaries. Trust requires three
things in order: attributable/reproducible verdicts, fail-closed containment,
and measured detection contribution. The revised sequence refuses to package
or market the result before all three are evidenced.

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
   Gates Stream 6. Engineering acceptance needs a multi-variant
   synthetic/declawed set beyond the 8 canaries plus a materially larger benign
   set. Any product-level claim additionally needs the externally managed,
   isolated validation corpus defined in §8.

## 11. Source

Workflow synthesis `extrace-real-tool-roadmap` (7-dimension gap assessment + 3
prioritization judges + synthesis), 2026-06-08. All file/line claims verified
against `main` @ `441cb72`.
