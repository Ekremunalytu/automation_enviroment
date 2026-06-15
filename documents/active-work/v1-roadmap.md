# ExTrace v1.0 Roadmap — From Finished Prototype To A Tool An Analyst Trusts Daily

`Last Updated: 2026-06-15`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: reliability-self-defense (v1.0 trust floor, Stream 1) — merged to main via PR #35 (week23 -> main, 653d807); closed v1.0 bars B1/B3/B4 plus self-defense fixes F-2/F-3. Tracker: documents/active-work/W23-reliability-self-defense.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

`Phase: Stream 1 (reliability-self-defense) MERGED to main via PR #35 (week23 -> main, 653d807) 2026-06-12. A new non-bar honesty stream (operator-console-honesty) is sequenced AHEAD of Stream 2 per user direction 2026-06-15 (plan in §5 "Next-Stream Plan"); Streams 2-8 keep their frozen numbers + bar→ID mappings and shift one week label; three post-v1.0 streams (operator-settings-ops, operator-disposition, network-egress-enforcement/mitmproxy) are added. All forward-planned; none open yet.`

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
| **★** | `operator-console-honesty` | Stop the console lying: dead/decorative Settings+System controls made honest | — (UI-only honesty) | non-bar |
| **2** | `reliability-multi-analyze` | Same appliance survives analyze #2, #3 on one container | B2 | yes |
| **3** | `verdict-provenance-reproducibility` (spine) | Same VSIX twice → same verdict; verdict bound to bytes | B5, B6 | yes |
| **4** | `operator-report-export` | Verdict can leave the tool as an actionable artifact | B9 | yes |
| **5** | `release-identity-ops` | Know the build, trust the green light, never lose history | B10 | yes |
| **6** | `measured-catch-rate` (mission core) | Detection asserted → measured; blind spots can't read CLEAN | B7, B8 | yes |
| **7** | `sequential-batch-corpus` | Point at a set, walk away, results table | — | post-v1.0 |
| **8** | `linux-host-hardening-evasion` | Shrink executor blast radius (Fedora-unblocked); extend evasion | — | post-v1.0 |
| **9** | `operator-settings-ops` | Server-persist settings; telemetry retention/purge; danger wipe/reset | — | post-v1.0 |
| **10** | `operator-disposition` | Operator marks benign-domain findings (raw vs adjusted; never deletes) | — | post-v1.0 |
| **11** | `network-egress-enforcement` (mitmproxy) | Real egress allow/deny + decrypted HTTP(S) evidence | — | post-v1.0 |

**Spine decision:** Stream 3 (reproducibility/provenance) precedes Stream 6
(measurement) — four downstream streams depend on a non-flickering, build-
attributable anchor. Getting that order wrong is the one mistake that lets the
project measure, calibrate, and scale on sand.

**Sequencing update (2026-06-15, user direction).** A non-bar
`operator-console-honesty` stream (★) is sequenced **first**; Streams 2-8 keep
their frozen numbers + bar→ID mappings and shift one week label. Streams 9-11 are
new post-v1.0 additions. Week-label cadence:
`W24 operator-console-honesty` → `W25 Stream 2 / B2` → `W26 Stream 3 / B5,B6 (spine)`
→ `W27 Stream 4 / B9` → `W28 Stream 5 / B10` → `W29 Stream 6 / B7,B8 → v1.0` →
post-v1.0 (Streams 7, 8, 9, 10, 11). Full detail + the mitmproxy ADR/spike gate are
in §5 "Next-Stream Plan (2026-06-15)".

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

#### Post-v1.0 streams added by this plan

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
- **Stream 11 `network-egress-enforcement` (mitmproxy)** — see below.

#### Stream 11 — `network-egress-enforcement`: mitmproxy as the interception engine (ADR + spike gated)

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
  the public CA cert; never baked into repo/image; generated per-install. Stream 11
  extends the B10 backup/restore mechanism delivered in W28 to include the CA
  volume; that extension is Stream 11 scope, not a W28 scope change.
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

**This makes real** the `strictNet` toggle and the `egress_allowlist` (both
honestly disabled "Not yet enforced" in W24). Depends on Stream 9
(`operator-settings-ops`) for allowlist persistence: **Stream 9 → Stream 11**.

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
- **W27 / B9** export carries no operator identity (download-focused GET); operator
  name persistence belongs to Stream 9.
- **W28 / B10** stays exactly its original scope (health DB probe + version identity
  + backup/restore); retention/settings/danger went to Stream 9, egress to Stream 11
  — no re-bloat.
- **W29 / B8** gate measures **raw** detection/FP only; disposition (Stream 10) is
  informational and post-v1.0.

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
- **★ operator-console-honesty** (sequenced first, non-bar) — `[CLEANUP settings-decorative-controls-honesty]`, `[CLEANUP system-mock-status-honesty]`, `[GOAL light-dark-theme]` (stretch; non-blocking).
- **Stream 9 operator-settings-ops** (post-v1.0) — `[GOAL operator-settings-server-persistence]`, `[GOAL telemetry-retention-purge]`, `[GOAL danger-zone-destructive-actions]`.
- **Stream 10 operator-disposition** (post-v1.0) — `[GOAL benign-domain-disposition]` (raw vs adjusted; never deletes; NOT in the B8 gate).
- **Stream 11 network-egress-enforcement** (post-v1.0, mitmproxy) — `[GOAL mitmproxy-tls-interception]` (ADR + spike gated; ADR stays `Proposed`), `[GOAL egress-allowlist-enforcement]`; depends on Stream 9.

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
