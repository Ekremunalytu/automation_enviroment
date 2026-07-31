# Static Analysis Pre-Check Lane

**Last Updated:** 2026-07-31 (active SMF measurement foundation adds
coverage-aware `INCONCLUSIVE`, deterministic rule/corpus fingerprints, the
container-only `make static-eval` evaluator, 32 MiB bounded production-bundle
coverage, and Node-style entrypoint resolution). Historical base: 2026-06-01
(ES-5 close-out — static result surfaced to the
API (`AnalyzeJobStatusResponse.static_report` / `static_report_path` +
`AnalyzeResponse.static_report`) and the UI (SimulationPage static pre-check
panel); ALLOW/WARN now persists the static-only combined bundle; the feature
flag was flipped **ON** after live Docker smoke evidence; ADR 0016 → Accepted.
The whole stream (ES-0..ES-5) is DONE). · **Post-ES-5 expansion** on branch
`extension-trigger-matrix` (2026-06-03): in-house static rules grew 6 → 10
(`s4` blacklisted-domain, `s5` suspicious-network-endpoint, `s6`
obfuscation-indicators, `s7` hardcoded-secret), Semgrep JS rules 4 → 8, plus a
dynamic `a7` blacklisted-domain rule and an operator-editable DB-backed
`blacklist_domains` denylist (seed ∪ operator). `s4` is HIGH but **WARNs** (NOT
added to the promoted-blocker frozenset — block-and-warn invariant unchanged).
See `documents/active-work/extension-trigger-matrix.md`. ·
**Security-development expansion** (2026-06-04): in-house static rules now load
**26 production rules** (`s1`-`s20` across multi-rule modules), adding the
webhook/crypto exfil surfaces (`s8`/`s9`), reverse-shell (`s10`), download-cradle
(`s11`), invisible-Unicode runs (`s12`), native `.node` loader/platform-gate/
host-context invoke (`s13`), globalState dormancy (`s14`), path-traversal server
(`s15`), cross-extension tamper (`s16`), credential-exfil (`s17`), download-exec
dropper (`s18`), the stylesheet-threat trio (`s19`), RMM-as-RAT abuse (`s20`),
and reserved-publisher spoof (`s1.reserved_publisher_spoof`). `s10`/`s11`/`s12`,
the GlassWorm-strength `s13` conjunction, the `s16` foreign-extension write, and
`s19.stylesheet_inline_js` are CRITICAL and block through the existing severity
gate; everything else WARNs — **no promoted-HIGH policy change**. The Semgrep JS
rule set grew to 16 advisory echoes. Status board + per-class specs live in
`documents/detection-design/README.md`.

Use this lane for the pre-execution static analysis stage: static
detection contracts, in-house static rules, the Semgrep runner, the
hardened `automation_static_analyzer` container, and the block-and-warn
decision gate that fronts the dynamic sandbox.

## Start Here

- `documents/adrs/0016-static-analysis-pre-check-stage.md`
- `documents/active-work/static-analysis-pre-check-stream.md`
- `documents/active-work/extrace-static-stream-handoff.md` (frozen
  design-intent source; field-level spec for every sub-iter)
- `packages/analysis_contracts/static_detection/` (landed ES-1)
- `static_runtime/rules/` + `static_runtime/static_runner.py` (landed ES-3a;
  rules live in the container-native package, NOT `packages/analysis_engine/`,
  so the hardened image stays minimal)
- `packages/analysis_contracts/typosquat_match.py` (landed ES-3a; shared
  stdlib-only matcher + `data/popular_extensions.txt`, reused by the dynamic
  `a3_typosquat` and the static `s2` rule — one allowlist copy, no engine import)
- `workflows/marketplace/static_analysis.py` (landed ES-3b — gate logic +
  container runner + `StaticAnalysisBlockedError`)
- `workflows/marketplace/analysis_service.py` (`_run_static_gate`) +
  `appcore/storage/crud_ops/analysis_jobs/static_gate.py`
  (`reject_analysis_job_static`) + `appcore/api/config.py`
  (`StaticAnalysisSettings`) (landed ES-3b — orchestrator wiring, the
  `rejected_static` transition, the feature flag)
- `appcore/contracts/schema_defs/marketplace.py` (ES-5 — `static_report` /
  `static_report_path` on `AnalyzeResponse` + `AnalyzeJobStatusResponse`) +
  `workflows/marketplace/analysis_reports.py` (`load_static_report_from_name`)
  + `workflows/marketplace/router.py` (GET `/analyze/{job_id}` folds the static
  report in) + `scripts/generate_ui_contracts.py` (static TS DTOs) +
  `ui/src/lib/adapters/job.ts` (`adaptStaticReport`) +
  `ui/src/features/simulation/SimulationPage.tsx` (static pre-check panel)
  (landed ES-5 — API/UI surfacing + ALLOW/WARN persistence + flag flip ON)
- **Post-ES-5 expansion (branch `extension-trigger-matrix`):**
  `static_runtime/rules/{s4_blacklisted_domain,s5_network_indicators,
  s6_obfuscation_indicators,s7_secret_exposure}.py` + the 8-rule
  `static_runtime/semgrep_rules/extrace-vsix-js.yml`; the shared stdlib-only
  matcher `packages/analysis_contracts/domain_indicators.py` (+ seed
  `data/blacklist_domains.txt`, mirrors `typosquat_match.py`) reused by the
  dynamic `packages/analysis_engine/rules/a7_blacklisted_domain.py`; the
  operator denylist via `workflows/detection_rules/blacklist_service.py` +
  `appcore/api/rules_router.py` + `appcore/storage/.../blacklist_domains.py` +
  Alembic `b3d9f1c2e7a4` (the `blacklist_domains` table). `main.py`
  primes the in-process override at boot (best-effort; DB-down is swallowed).
- **Security-development expansion (multi-class custom rule stream):**
  `static_runtime/rules/{s8_exfil_webhook,s9_crypto_address_scan,
  s10_reverse_shell,s11_download_cradle,s12_invisible_unicode,
  s13_native_node_loader,s14_globalstate_dormancy,s15_path_traversal_server,
  s16_cross_extension_tamper,s17_credential_exfil,s18_download_exec_dropper,
  s19_stylesheet_threats,s20_rmm_remote_access}.py` + the
  `s1.reserved_publisher_spoof` manifest rule; the matching
  `static_runtime/semgrep_rules/extrace-vsix-js.yml` echoes; the
  `_common.TEXT_SUFFIXES` `.less`/`.scss`/`.sass` coverage fix; the curated
  real-C2/relay host additions in
  `packages/analysis_contracts/data/blacklist_domains.txt` (snowshono Stage-3
  relay + related-campaign hosts + kagema `niggboo.com`); and the per-class
  design specs under `documents/detection-design/`. SHA-256 hashes stay
  reference-only and shared Google Calendar/Gmail fallback infrastructure is
  intentionally not denylisted (pinned by `tests/security/test_ioc_safety.py`).
  The full status board is `documents/detection-design/README.md`.
- **Measurement-foundation expansion (active):**
  `documents/active-work/static-analysis-measurement-foundation.md` owns
  SMF-0..SMF-8 acceptance. `packages/analysis_contracts/static_evaluation/`
  defines the safe corpus/evaluation contracts; `static_runtime/evaluation.py`
  invokes the production runner and policy in the same networkless container.

## Invariants

- **Schema-first.** Pydantic contracts land before any tool runner; tools
  map into the schema, never the reverse.
- **Enum reuse by identity.** `Severity` / `Confidence` / `RuleLifecycle`
  / `AdversaryClass` come from `packages.analysis_contracts`, not parallel
  clones (ADR 0005 packages charter).
- **Minimal-image import boundary.** The static rules + runner live in
  `static_runtime/` and import only the standard library +
  `packages.analysis_contracts` — never `workflows`, `executor`, `appcore`,
  `ui`, or `packages.analysis_engine` (whose `__init__` eagerly imports the
  dynamic engine, which would bloat the hardened image). Pinned by
  `tests/architecture/test_static_runtime_import_boundary.py`.
- **Block/inconclusive/warn/allow.** CRITICAL → terminal `rejected_static`; the only
  promoted HIGH blocker is `extrace.s2.typosquat` via a frozenset, not
  config. Schema-valid incomplete coverage without a blocker concludes
  `INCONCLUSIVE`; real warning IDs remain separate from bounded coverage causes.
  Precedence is `BLOCK > INCONCLUSIVE > WARN > ALLOW`.
- **Bounded production bundles.** In-house text rules and Semgrep share a
  32 MiB per-file ceiling under the unchanged 30-second outer budget. Larger
  targets remain visible and inconclusive. Intentional Semgrep vendor/minified
  exclusions stay inventory-visible but are not alone a degraded tool state;
  in-house rules retain bounded text coverage.
- **Container isolation.** The static analyzer runs with `network_mode:
  none`, `cap_drop: [ALL]`, `no-new-privileges`, non-root, no
  `docker.sock` — never inline on the host or in the executor.
- **Feature-flagged.** `settings.static_analysis.ENABLED` is **ON** (flipped at
  the ES-5 close-out, 2026-06-01, after live Docker smoke evidence passed). A
  swallowed tool error / timeout surfaces through
  `StaticToolExecutionRecord.status` + `StaticDetectionReport.partial`
  (observability v2), never a silent ALLOW. The timeout budget is
  `TIMEOUT_BUDGET_S` on both the app and executor config mirrors (env
  `STATIC_ANALYSIS_TIMEOUT_BUDGET_S`).

## Tests And Checks

- `make check-all` with `postgres_test` up (the strict per-sub-iter gate).
- `make test-security` — enroll new static security tests into the
  explicit file list in the Makefile; it does not auto-discover.
- `make test-smoke` for the container + pipeline sub-iters.
- `make static-eval SPLIT=tuning|holdout|all` for deterministic SMF corpus
  measurement; JSON is canonical and Markdown derives from it.
- `make static-up` / `make static-run-fixture` for manual container spot
  checks (land ES-2).

## Open Subsystem Doc Only If Needed

- `extrace-static-stream-handoff.md` — the authoritative field-level spec
  (contract invariant lists, v2 Literal pre-ship sets, the ES-1 →
  ES-3b step-Literal regression mitigation). Open it for any sub-iter
  detail this lane summarizes.
- `documents/agent-lanes/security-detection.md` — the dynamic detection
  lane; the static findings extend its taxonomy (ADR 0003).
- `documents/agent-lanes/platform-storage.md` — for the `rejected_static`
  status + `static_report_path` column + Alembic migration (ES-1).
- `documents/POST_POC_BACKLOG.md` → `[GOAL mitre-coverage-*]` (Contracts /
  Reports / Detection) — the downstream W23 MITRE ATT&CK coverage matrix that
  consumes this lane's rule catalog + static findings (a `/mitre` UI surface +
  `GET /api/mitre/catalog`). The backend catalog is independent of this stream;
  the per-report static overlay depends on ES-3b populating `static_report_path`.

## Avoid

- Bending the static-detection schema to fit a tool's output.
- Importing `packages.analysis_engine` (or `workflows`/`appcore`) from
  `static_runtime/` — it drags the dynamic engine into the hardened image.
- Running the static analyzer inline on the host or in the executor.
- Widening `uq_analysis_jobs_single_active` to include `rejected_static`
  (it is terminal).
- Extending `ANALYSIS_JOB_STEP_NAMES` without updating `empty_job_steps`
  in the same commit (the documented ES-1 regression).
- Any external network from the static container (Semgrep runs offline,
  `--metrics=off`).
