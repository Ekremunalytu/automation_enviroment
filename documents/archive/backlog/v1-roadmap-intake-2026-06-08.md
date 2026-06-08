# v1.0 Roadmap Intake Detail Snapshot — 2026-06-08

Archived detail for the `POST_POC_BACKLOG.md` intake titled
"Newly Captured (v1.0 roadmap intake 2026-06-08)". The canonical backlog keeps
only the compact stable-ID map; this snapshot preserves the evidence and
disposition notes that fed the forward tracker at
[`../../active-work/v1-roadmap.md`](../../active-work/v1-roadmap.md).

Roadmap state: planning only. `podman-airgapped-deploy` remains the active stream
pointer until `reliability-self-defense` opens on explicit user go-ahead.

Existing IDs re-homed by the roadmap:

- `[FOLLOWUP vsix-entry-log-sanitization]` → Stream 4.
- `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` → Stream 2.
- `[FOLLOWUP harness-secret-distribution-redesign]` → Stream 8.

## Stream 1 — reliability-self-defense

| Stable ID | Sev | Evidence | Disposition |
|---|---|---|---|
| `[BUG report-builder-unbounded-pem-redact]` (audit F-1) | Medium | `executor/flows/playwright/report_builder.py:292/294` calls `redact_secrets`; `packages/analysis_contracts/evidence.py:84` still iterates the unbounded `(?:.|\n)*?` `private_key` pattern at `evidence.py:56-62`; the bounded `_redact_private_key_bounded` scanner is reachable only via `redact_multiline_secrets`. ReDoS stall on adversarial ext-host trace with 200+ unmatched `BEGIN` markers. CRSC-2 / W13-7 regression. | Stream 1 / S1 — blocking. Fix at source so every `redact_secrets` call site is bounded; regression test via the report-build path. |
| `[BUG wedged-job-no-same-boot-recovery]` | Med/High | No `last_heartbeat_at` column on `appcore/storage/model_defs/analysis_job.py`; the boot-id reaper only fires on process restart; a hung or out-of-taxonomy crashing worker holds the single-active queue until API restart. `workflows/marketplace/analysis_service.py:600/607` catches only the analyze taxonomy. | Stream 1 / S2. Heartbeat column + stale-running reaper releasing same-boot jobs + narrow boundary guard that writes `fail_job` then re-raises. No bare `except`. |
| `[FOLLOWUP offline-vsix-size-bound]` (audit F-2) | Low | `workflows/marketplace/offline.py:178,229` uses `path.read_bytes()` before any outer `.vsix` size cap; the inner manifest/archive caps do not prevent a huge file from being loaded into memory during listing/intake. | Stream 1 / S3. Add `st_size` pre-check, reusing the `vsix_max_uncompressed_size` family; return clean 413/422 before `read_bytes()`. |
| `[BUG import-graph-relative-import-gate-gap]` (audit F-3) | Low | `tests/architecture/test_import_graph_facades.py:38` skips every relative `ImportFrom` through `if node.level: continue`, leaving a latent boundary-gate escape. | Stream 1 / S3. Resolve `node.level` relative imports to absolute module names and run them through the banned-root check; mirror the same handling in the static-runtime counterpart if present. |
| `[BUG verdict-color-inconclusive-renders-clean]` | High (safety) | `ui/src/features/reports/verdictColors.ts` defines a 5-state palette but is imported nowhere; `ui/src/features/reports/ReportsPage.tsx:85/191` collapses verdict states into severity tones, mapping everything except `malicious`/`suspicious` to `low`/`ok`. `ui/src/features/simulation/SimulationPage.tsx:391` maps inconclusive health to neutral rather than a stop tone. | Stream 1 / S4 — blocking. Wire the palette into report and simulation verdict surfaces; INCONCLUSIVE must be a non-green STOP; snapshot tests assert `inconclusive` and `clean_with_notes` never render the clean tone; add compact legend + recommended action copy. |
| `[FOLLOWUP exthost-logparse-redos-bounds-sweep]` | uncharacterized | The ext-host parse/marker regex family (`extension_host_log_parse.py`, `extension_host_strace_parse.py`, `executor/host.py:65`, `health/handshake.py:37`) was not fully audited for ReDoS shape, in the same risk family as F-1. | Stream 1 / S5 — non-blocking. Audit and document the result; if reclassified as line-anchored/linear, add per-line length cap as hygiene and close the standing "unaudited" flag. |

## Stream 3 — verdict-provenance-reproducibility

| Stable ID | Sev | Evidence | Disposition |
|---|---|---|---|
| `[GOAL vsix-content-sha256-provenance]` | Med/High | No artifact hash is persisted on `AnalysisJob` or `Extension`, so an analyst cannot prove a report belongs to the exact bytes scanned; same `(publisher, name, version)` bytes can be conflated. | Stream 3. Compute `vsix_sha256` at download and offline intake; persist on `AnalysisJob` with Alembic; stamp into ActivationReport/DetectionReport through the additive contract procedure. |
| `[GOAL verdict-reproducibility-anchor]` | High | Live `run_quality` can vary between runs on identical inputs: reason counts swing, `harness_verification_unconfirmed_present` flickers, unresolved counts vary, and status can flip `degraded`/`inconclusive`. | Stream 3. Partition verdict-affecting behavioral reasons from harness-health variance; keep verdict label deterministic and surface residual variance as an explicit band. Time-box: ship band reframing first if full determinism is too deep. |

## Stream 4 — operator-report-export

| Stable ID | Sev | Evidence | Disposition |
|---|---|---|---|
| `[GOAL report-export-artifact]` | Med | No report-export endpoint; `Content-Disposition` is absent from the app surface. The verdict cannot leave the Reports tab to feed a ticket or IR workflow. | Stream 4. Add one backend endpoint returning a self-contained verdict + findings + mitigations + evidence artifact, JSON first and printable HTML later; stamp sha256 and version; add Export button. Keep it a read-side projection off stored `extra=forbid` contracts. |
| `[FOLLOWUP vsix-entry-log-sanitization]` | Med/High | `workflows/marketplace/client.py:269/319` logs raw rejected VSIX entry names, which can contain adversarial archive paths. | Stream 4. Sanitize/log-shape raw entry names alongside offline skip-reason UX. |

## Stream 5 — release-identity-ops

| Stable ID | Sev | Evidence | Disposition |
|---|---|---|---|
| `[CLEANUP version-identity-coherence]` | Med | Version strings are incoherent: `pyproject.toml` and app config are `1.0.0`, UI is `0.0.0`, `RULES_VERSION` is `0.0.0`, there are no git tags, and the Podman bundle defaults to mutable `latest`. | Stream 5. One version source + assert-equal test; git tag; versioned bundle tag; stamp `app_version` / build into report builders. |
| `[GOAL api-health-db-probe]` | Med | `appcore/api/health_router.py:19` returns static app health, so green `/api/health` does not prove the API can talk to DB. | Stream 5. `/api/health` runs `SELECT 1` and reports DB status; add API container healthcheck in compose/Podman control. |
| `[GOAL podman-backup-restore]` | Med | `deploy/podman/extrace-ctl.sh` has `destroy` but no `backup` / `restore`; an operator upgrade mistake can lose scan history. | Stream 5. Add `extrace-ctl.sh backup` / `restore` using `pg_dump` / `pg_restore`, destroy confirmation, and upgrade/rollback runbook. Live-validate on Fedora. |

## Stream 6 — measured-catch-rate

| Stable ID | Sev | Evidence | Disposition |
|---|---|---|---|
| `[GOAL measured-catch-rate-corpus]` | High (mission) | Detection is asserted against 7 A-series synthetic canaries plus `t1-demo-runnable-canary`; there is no aggregate precision/recall measurement. | Stream 6. Labeled corpus with multi-variant adversarially shaped synthetic/declawed variants plus real benign controls; emit per-family caught/missed/FP; reuse `analyze_fixture`; no new dependencies; `LABEL.yaml` carries `must_fire` / `must_not_fire`. |
| `[GOAL benign-false-positive-gate]` | High (trust) | No benign-FP gating scan exists, so CLEAN verdict FP rate is asserted rather than measured. | Stream 6. FP gating scan over real extensions such as ms-python, eslint, prettier, copilot, and pylance with an explicit FP budget; CI fails when rule edits exceed it. |
| `[GOAL platform-blind-verdict-annotation]` | Med (false-neg) | A win32/darwin-gated family that static convicts but Linux dynamic cannot exercise can appear as a clean dynamic pass. | Stream 6. Report a "dynamic platform-blind" state so clean dynamic pass never implies CLEAN where the sandbox cannot structurally exercise the behavior. |
| `[GOAL adr-0015-e1-e2-evasion-detection]` | High (false-neg) | ADR 0015 sandbox-evasion is policy + observer-side canary only; a probe-then-dormant extension remains a true false-negative. | Stream 6. Add E1/E2 detection recorders for webdriver presence and CDP fingerprint via the reserved harness OutputChannel; route probe-then-dormant to inconclusive/suspicious with explicit evasion reason. No masking in v1. |

## Streams 7-8 — post-v1.0

| Stable ID | Evidence / scope | Disposition |
|---|---|---|
| `[GOAL sequential-batch-corpus]` | No batch/corpus concept exists. | Stream 7. `analysis_runs` parent via `crud.py`, one in-process serial drain loop respecting the single-active index, per-item exception isolation, restart-survivable progress, and batch UI. No Redis/Celery/parallel/k8s. Depends on Streams 2 and 6. |
| `[GOAL container-hardening-ratchet-down]` | ADR 0013 deferred `read_only:true`, tmpfs, and custom seccomp hardening; Fedora is now unblockable. | Stream 8. Needs sustained Linux validation on the target host. |
| `[GOAL adr-0015-e3-e5-evasion-detection]` | Timing, platform-identity, and process-evasion detection records lean on the Stream 8 hardening baseline. | Stream 8. Full E1-E5 masking is XL; v1 caps at E1/E2 detection. |
