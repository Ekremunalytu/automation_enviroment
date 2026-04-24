# ExTrace Codebase Quality & Architecture Report

## 1. Executive Summary

ExTrace is currently closer to a clean modular monolith than to spaghetti code, but the risk is concentrated in one area: the dynamic execution / Playwright / runtime reporting pipeline. The top-level architecture is mostly sensible for a local-first defensive security tool: `appcore/` owns platform and storage, `workflows/` owns API-facing business flows, `executor/` owns sandbox execution, `packages/` owns framework-agnostic contracts/planning/detection, and `ui/` is isolated frontend code.

Main strengths:

- The repository has explicit architectural boundaries, including import-graph tests that prevent `packages/` from importing runtime/web/storage layers.
- `main.py` is clean and only wires the three workflow routers.
- The system enforces a single-worker API assumption, which matches the local-first single-user product scope.
- Detection logic is isolated under `packages/analysis_engine/`.
- Reports are validated against Pydantic contracts before write, and report writes are atomic.
- The code has invested in automation health, run quality, scenario traces, skipped scenarios, and report honesty. That is important for a security tool.

Main weaknesses:

- The executor/Playwright layer has several large orchestration files that are becoming difficult to reason about: `entrypoint_runner.py`, `monitor_lifecycle.py`, `monitor_types.py`, `stimulus_passes.py`, `health_reconciliation.py`.
- `ActivationReport` is becoming a large universal report object carrying raw events, health, summaries, risk metadata, scenario traces, coverage, log state, and evidence state.
- Some security-sensitive path generation uses raw `publisher`, `name`, and `version` values.
- VSIX extraction has ZipSlip protection, but does not appear to enforce archive size, file count, or decompressed-size limits.
- The API container has Docker socket access. That is understandable for a local sandbox controller, but it is a major trust boundary and must stay explicitly local.
- noVNC and CDP are exposed for local debugging. That is useful, but unsafe if exposed beyond localhost.
- Test coverage is broad, but several test files have become very large and harder to maintain.

Biggest spaghetti-code risk:

- Dynamic execution state is accumulating in `executor/flows/playwright/`, especially around monitor lifecycle, event attempts, health reconciliation, scenario execution, and report finalization.

Biggest overengineering risk:

- The project may drift into generic planner / event / compatibility layers when direct typed contracts and explicit sequential flows are enough.

Biggest security-sensitive risks:

- Path traversal through untrusted marketplace identity fields.
- Shell injection-like behavior inside the executor through URI trigger terminal commands.
- Resource exhaustion through unbounded VSIX extraction.
- Treating Docker/noVNC/CDP exposure as implicitly safe rather than explicitly local-only.

The project is still moving toward a clean modular monolith, not away from it, but only if the executor/reporting layer is kept under control.

Architecture status: **Mostly healthy with risks**

Justification: the top-level boundaries are good and actively enforced, but the dynamic execution/reporting subsystem is large, stateful, security-sensitive, and already showing pressure toward god objects and broad mutable report state.

## 2. Repository Structure Assessment

### `main.py`

Ownership: FastAPI app creation and router wiring.

Assessment: Clear and appropriately small. It validates `API_WORKERS == 1`, which matches the single-user local architecture. It includes only:

- extension catalog router
- activation reports router
- marketplace router

Recommendation: Keep as-is. Do not let business logic move into `main.py`.

### `appcore/`

Ownership: API configuration, DB session, contracts, storage models, CRUD.

Assessment: Responsibility is mostly clear. Storage writes correctly route through `appcore/storage/crud.py` and `crud_ops/`. SQLAlchemy models are centralized under `appcore/storage/model_defs/`.

Risk: Low.

Concern: configuration defaults are not fully aligned with the local security posture. `API_CORS_ALLOW_ORIGINS="*"` and default `API_CORS_ALLOW_CREDENTIALS=True` are loose defaults, even though Compose overrides credentials to false.

Recommendation: Keep `appcore/` as the platform layer. Tighten defaults where safe, but do not add a large config framework.

### `workflows/extension_catalog/`

Ownership: extension manifest reading, parsing, catalog persistence.

Assessment: Mostly cohesive. `manifest_reader.py` and `manifest_parser.py` are clear. `service.py` is long but still largely acts as an application service around parsing, validation, and CRUD.

Overlap: Some parsing and validation responsibilities are split between contracts and parser code. This is acceptable because VS Code manifests are flexible.

Risk: Low to Medium.

Recommendation: Keep as-is for now. If touched, reduce docstring noise and keep parsing helpers small.

### `workflows/marketplace/`

Ownership: marketplace search/download, VSIX extraction, analysis job orchestration, trigger generation, analysis report loading.

Assessment: This is a major integration boundary and is appropriately larger than other workflows. The split between `client.py`, `analysis_service.py`, `analysis_execution.py`, `analysis_reports.py`, `job_service.py`, and `trigger_service.py` is better than one giant marketplace module.

Overlap: `client.py`, `trigger_service.py`, `analysis_execution.py`, and `executor/host.py` all participate in artifact path construction or execution flow. Identity/path safety should be centralized.

Risk: Medium.

Recommendation: Keep module split. Add a small shared safe artifact-name/path helper rather than adding new layers.

### `workflows/activation_reports/`

Ownership: report listing and retrieval.

Assessment: Clear and small compared with the executor/reporting code.

Risk: Low.

Recommendation: Keep thin. Do not move report interpretation here; report semantics should stay in contracts/report builder/detection.

### `executor/`

Ownership: Docker control, sandbox interaction, VS Code automation, runtime capture, Playwright flows.

Assessment: Correctly separated from `workflows/` through `executor/control.py`. The `executor/flows/playwright/` subtree is the main complexity center.

Risk: Medium to High.

Concern: Several executor modules are individually cohesive, but together form a dense runtime state machine. This is the area most likely to become spaghetti if feature work continues without cleanup.

Recommendation: Preserve the boundary, but continue splitting lifecycle, capture, attempt ledger, health reconciliation, and report building into explicit modules.

### `executor/container/`

Ownership: container image, startup scripts, VS Code launch, noVNC/CDP surfaces.

Assessment: Practical and understandable. The container runs as a non-root user, verifies harness files, and writes deterministic settings. It also launches VS Code with `--no-sandbox`, exposes noVNC without a password, and exposes CDP.

Risk: Medium.

Recommendation: Accept this only as a local sandbox appliance design. Document and enforce localhost-only expectations.

### `packages/`

Ownership: framework-agnostic contracts, planner, detection engine.

Assessment: This is one of the strongest architecture choices in the repo. `packages/analysis_contracts/`, `packages/analysis_planner/`, and `packages/analysis_engine/` are the right places for stable contracts and explainable detection.

Risk: Low to Medium.

Concern: `packages/analysis_planner/registry.py` is large and can become a generic planning framework. That is acceptable only if it remains directly driven by real activation scenarios.

Recommendation: Keep `packages/` framework-agnostic. Avoid making it a plugin system.

### `ui/`

Ownership: frontend.

Assessment: Not deeply inspected in this pass. The repository shape suggests the UI is separated under `ui/src/app/`, `ui/src/features/`, `ui/src/components/`, and `ui/src/lib/`.

Risk: Unknown to Medium.

Recommendation: UI should consume typed API/report contracts and avoid duplicating detection logic.

### `tests/`

Ownership: platform, workflow, executor, scanner, smoke, security tests.

Assessment: Test coverage appears broad. Architecture tests are a major strength. Some test files are very large, especially marketplace router and executor monitor tests.

Risk: Medium.

Recommendation: Split large tests by behavior area when they are next touched. Do not do a test rewrite just for aesthetics.

### `docker/`

Ownership: API image.

Assessment: Mostly clear, but there is an odd empty-looking `docker/api 2` directory. That looks like workspace clutter or an abandoned copy.

Risk: Low.

Recommendation: Remove only after confirming it is unused and not user-owned work.

## 3. Main Execution Flow

### 1. App startup

Relevant files:

- `main.py`
- `appcore/api/config.py`
- `appcore/db/session.py`
- `workflows/marketplace/job_service.py`

What happens:

- FastAPI app is created.
- Runtime settings are validated.
- Routers are included.
- Interrupted analysis jobs are recovered.

Boundary quality: Good.

Concern: The single-worker assumption is explicit and correct. This should remain part of the architecture unless the whole job model is redesigned.

### 2. Marketplace search/download

Relevant files:

- `workflows/marketplace/router.py`
- `workflows/marketplace/client.py`
- `workflows/extension_catalog/service.py`

What happens:

- API receives marketplace search or download requests.
- Marketplace client queries the VS Marketplace API.
- VSIX is downloaded.
- ZIP members under `extension/` are extracted.
- `package.json` is loaded and validated.
- Extension metadata is persisted through catalog service and CRUD.

Boundary quality: Mostly good.

Concern: ZIP member traversal is checked, but artifact paths are derived from raw identity fields. This is a security-sensitive gap.

### 3. Catalog ingestion

Relevant files:

- `workflows/extension_catalog/manifest_reader.py`
- `workflows/extension_catalog/manifest_parser.py`
- `workflows/extension_catalog/service.py`
- `appcore/contracts/schema_defs/catalog.py`
- `appcore/storage/crud_ops/writes.py`

What happens:

- `package.json` is read.
- Manifest fields are parsed into capabilities, scripts, activation events, contributes, and extra fields.
- Pydantic schemas validate the data.
- Storage layer persists via CRUD.

Boundary quality: Good.

Concern: The parser tolerates malformed manifest fields by skipping them in places. That is useful for robustness but can hide adversarial weirdness unless warnings/health fields preserve what was ignored.

### 4. Analysis job creation

Relevant files:

- `workflows/marketplace/router.py`
- `workflows/marketplace/job_service.py`
- `appcore/storage/crud_ops/analysis_jobs.py`

What happens:

- API checks that the requested VSIX exists.
- A single active analysis job is reserved.
- A background thread is started for local execution.
- Job state is persisted in the database.

Boundary quality: Acceptable for local single-user scope.

Concern: Direct background threads are fine here. Do not replace this with Celery or a queue unless the product scope changes.

### 5. Trigger planning

Relevant files:

- `workflows/marketplace/trigger_service.py`
- `packages/analysis_planner/`
- `packages/analysis_contracts/contracts.py`

What happens:

- Stored manifest metadata is loaded.
- Activation events, contributes, capabilities, scripts, and extension identity are converted into a `TriggerPayload`.
- Trigger JSON is written for the executor.

Boundary quality: Medium.

Concern: `trigger_service.build_trigger_payload()` is a boundary pinch point. It knows DB shapes, manifest contribution shapes, planner input expectations, and file output details.

### 6. Sandbox preparation and VS Code control

Relevant files:

- `executor/control.py`
- `executor/host.py`
- `executor/container/start.sh`
- `executor/container/launch_vscode.sh`

What happens:

- Workflows call the thin executor control boundary.
- Docker Compose commands reset/reload/install/run automation.
- The executor container launches VS Code with harness extension, noVNC, and CDP.

Boundary quality: Good at the Python import level; security boundary must be treated carefully.

Concern: API has Docker socket access. That is a powerful local control plane.

### 7. Playwright execution and stimulus simulation

Relevant files:

- `executor/flows/playwright/entrypoint_runner.py`
- `executor/flows/playwright/automation.py`
- `executor/flows/playwright/stimulus_passes.py`
- `executor/flows/playwright/stimulus_attempts.py`
- `executor/flows/playwright/entrypoint_triggers.py`

What happens:

- Executor connects to VS Code over CDP.
- Trigger payload is loaded.
- Scenarios are selected.
- Playwright simulates UI behavior.
- Layered event passes attempt activation.
- Runtime capture and event attempts are recorded.

Boundary quality: Medium.

Concern: This is the most complex execution path. The code is procedural and testable, but several functions now do orchestration, failure classification, event recording, and report-state updates together.

### 8. Runtime capture

Relevant files:

- `executor/flows/playwright/runtime_capture/network.py`
- `executor/flows/playwright/runtime_capture/filesystem.py`
- `executor/flows/playwright/runtime_capture/processes.py`
- `executor/flows/playwright/runtime_capture/extension_host.py`

What happens:

- Network, file, process, and extension-host signals are collected.
- Events are normalized and attributed where possible.
- Capture errors are preserved in report health.

Boundary quality: Good conceptually.

Concern: Event attribution is necessarily heuristic. It should remain conservative and evidence-backed.

### 9. Report building and validation

Relevant files:

- `executor/flows/playwright/monitor_lifecycle.py`
- `executor/flows/playwright/monitor_types.py`
- `executor/flows/playwright/report_builder.py`
- `packages/analysis_contracts/contracts.py`
- `packages/analysis_contracts/report_invariants.py`

What happens:

- Runtime monitor state is converted into an activation report.
- Report health, run quality, scenario traces, attempts, logs, and evidence are serialized.
- Pydantic contract validation runs before writing.
- Report is written atomically.

Boundary quality: Strong validation, but state ownership is broad.

Concern: `ActivationReport` is the main data-model pressure point.

### 10. Detection and API report response

Relevant files:

- `workflows/marketplace/analysis_reports.py`
- `packages/analysis_engine/runner.py`
- `packages/analysis_engine/rules/`
- `packages/analysis_contracts/detection/`

What happens:

- Completed activation report is loaded.
- Detection engine runs production rules.
- Detection bundle is attached to API response.

Boundary quality: Good.

Concern: Detection depends on report quality. Failed or partial dynamic runs must never be interpreted as clean results.

## 4. Module Boundary Review

| Boundary | Current State | Risk | Evidence | Recommended Improvement |
|---|---|---:|---|---|
| Ingestion and parsing | Mostly clean | Low | `manifest_reader.py`, `manifest_parser.py`, `service.py` are separate | Preserve split; surface malformed skipped fields as warnings when useful |
| Static metadata and dynamic execution | Mostly clean | Medium | `workflows/marketplace/trigger_service.py` bridges DB metadata to executor payload | Keep bridge explicit; do not let executor read DB directly |
| Sandbox orchestration and detection | Clean | Low | Detection lives in `packages/analysis_engine/`, executor does not run detection rules | Keep detection out of executor |
| Playwright automation and behavioral analysis | Mixed but contained | Medium | `stimulus_passes.py`, `monitor_lifecycle.py`, `health_reconciliation.py` share scenario, attempts, and health state | Split attempt ledger and health reconciliation from UI-driving code |
| Logging/tracing and detection | Mostly clean | Medium | Detection consumes normalized report events rather than raw logs | Continue normalizing events before detection; avoid rules parsing log text directly |
| Backend/API and domain logic | Mostly clean | Medium | Routers are mostly thin; marketplace router still builds some response semantics | Keep routers thin; move response interpretation into workflow helpers |
| Reporting and raw event collection | Partially mixed | High | `ExtensionMonitor` captures events, tracks attempts, computes derived state, and persists report | Keep monitor API, but move capture lifecycle, ledger, and report finalization into separate helpers |
| Infrastructure and domain code | Mostly clean | Medium | `executor/control.py` is a good boundary; Docker details mostly in `executor/host.py` | Preserve `executor.control` as the only workflow import boundary |

## 5. Spaghetti-Code Risk Analysis

### Issue: Playwright Entrypoint Owns Too Much

Location:

- `executor/flows/playwright/entrypoint_runner.py`
- `main()`
- `run_with_dependencies()`

Problem:

The entrypoint coordinates CLI parsing, CDP connection, trigger loading, monitor startup, reload behavior, execution-mode dispatch, report finalization, error handling, and exit-code policy.

Why it matters:

This file becomes the place every dynamic-analysis feature wants to touch. That increases regression risk around failure modes, especially because dynamic analysis correctness depends on exact sequencing.

Risk level: High.

Recommended fix:

Extract execution-mode dispatch and report-finalization policy into small helpers. Keep the public CLI entrypoint stable.

### Issue: Extension Monitor Is a God Object

Location:

- `executor/flows/playwright/monitor_lifecycle.py`
- `ExtensionMonitor`

Problem:

`ExtensionMonitor` starts/stops capture, attaches runtime tracers, records scenario traces, records event attempts, reconciles activation state, computes derived report state, handles live persistence, and finalizes monitor output.

Why it matters:

Monitor correctness is security-critical. When capture, attribution, attempts, and report state are all owned by one object, it becomes hard to prove whether a missing signal means "clean extension," "failed automation," or "capture bug."

Risk level: High.

Recommended fix:

Keep `ExtensionMonitor` as the facade, but move ledger operations, capture lifecycle, and report-state refresh into explicit helper modules with narrow inputs/outputs.

### Issue: Giant Mutable Activation Report

Location:

- `executor/flows/playwright/monitor_types.py`
- `ActivationReport`
- `packages/analysis_contracts/contracts.py`
- `ActivationReport`

Problem:

The runtime report object and serialized report contract carry identity, raw logs, network/file/process events, scenario traces, event attempts, summaries, health, coverage, risk metadata, and signal summaries.

Why it matters:

A giant report object encourages every layer to mutate or depend on everything. Over time, this becomes an implicit global state container for the analysis run.

Risk level: High.

Recommended fix:

Do not rewrite the report. Instead, introduce small typed submodels for the most unstable dict fields first: `automation_health`, `run_quality`, `log_health`, `coverage_summary`, and `signal_summary`.

### Issue: Raw Dictionaries in Layered Stimulus Flow

Location:

- `executor/flows/playwright/stimulus_passes.py`
- `executor/flows/playwright/stimulus_attempts.py`
- `packages/analysis_planner/attempts.py`

Problem:

Layered activation attempts move through several layers with dictionary-like payloads and flexible `Any` fields.

Why it matters:

This is exactly where deterministic behavior matters. Raw dictionaries make it easier for planner/executor/report contracts to drift silently.

Risk level: Medium.

Recommended fix:

Use small dataclasses or Pydantic models at the planner-to-executor boundary for attempt inputs and attempt outcomes.

### Issue: Compatibility Facades Can Hide Ownership

Location:

- `executor/flows/playwright/monitor.py`
- `executor/flows/playwright/attribution/__init__.py`

Problem:

The facades re-export a large surface to preserve legacy imports.

Why it matters:

Compatibility facades are acceptable during refactors, but if new logic is added there, they become dumping grounds.

Risk level: Medium.

Recommended fix:

Freeze facades as import shims. Add new logic only to implementation modules.

### Issue: Trigger Service Is a Boundary Pinch Point

Location:

- `workflows/marketplace/trigger_service.py`
- `build_trigger_payload()`

Problem:

This function maps database rows, manifest metadata, contribution points, planner inputs, output paths, and trigger payload creation.

Why it matters:

It is a natural place for static-analysis, planner, and executor assumptions to become tangled.

Risk level: Medium.

Recommended fix:

Split only the pure mapping helpers: identity extraction, contribution metadata extraction, and output path creation. Avoid adding a new service layer.

### Issue: Large Test Files Obscure Behavior

Location:

- `tests/workflows/marketplace/test_router.py`
- `tests/executor/test_playwright_monitor_attribution.py`
- `tests/executor/test_playwright_helpers.py`
- `tests/executor/test_playwright_entrypoint.py`

Problem:

Some test files exceed production module size and cover many behaviors at once.

Why it matters:

Large test files become hard to use as executable documentation. They also make targeted changes slower.

Risk level: Low to Medium.

Recommended fix:

Split tests by behavior when touched: job lifecycle, report health, attribution, fatal UI recovery, marketplace download, and trigger planning.

## 6. Overengineering Risk Analysis

### Issue: Job Snapshot Dictionaries

Location:

- `workflows/marketplace/job_service.py`

Problem:

Job snapshots are created and passed as plain dictionaries, then validated into response schemas.

Why it is overengineered:

For a local single-user tool, a small typed internal snapshot would be easier to debug than repeated dict construction and response validation.

Simpler alternative:

Use an internal `AnalysisJobSnapshot` dataclass or Pydantic model and convert once at the API boundary.

Risk level: Low.

### Issue: Planner Registry Size

Location:

- `packages/analysis_planner/registry.py`

Problem:

The planner registry is large and can drift into a generic activation framework.

Why it is overengineered:

The project does need a planner, but it does not need a plugin framework or abstract scenario marketplace.

Simpler alternative:

Keep the registry explicit and scenario-driven. Add new planner entries only when a real activation surface requires them.

Risk level: Medium.

### Issue: Custom Dependency Seams in Entrypoint

Location:

- `executor/flows/playwright/entrypoint_runner.py`

Problem:

The entrypoint exposes many dependency override seams for testing.

Why it is overengineered:

This is useful for tests, but if expanded further it becomes a homegrown dependency injection container.

Simpler alternative:

Keep current seams stable. Do not generalize them. Extract pure helpers instead.

Risk level: Low to Medium.

### Issue: Database Pool Defaults Too Large

Location:

- `appcore/api/config.py`
- `DatabaseSettings`

Problem:

Defaults like pool size 20 and max overflow 40 are high for a local single-user service.

Why it is overengineered:

The product is explicitly not high-concurrency.

Simpler alternative:

Use smaller defaults unless tests or local workflows prove otherwise.

Risk level: Low.

### Issue: Compatibility Shims Becoming Permanent Architecture

Location:

- `executor/flows/playwright/monitor.py`
- `executor/flows/playwright/attribution/__init__.py`

Problem:

Large re-export files preserve legacy import paths.

Why it is overengineered:

They are transitional tools, not architectural surfaces.

Simpler alternative:

Keep them as thin shims and prevent new code from importing through them unless compatibility requires it.

Risk level: Medium.

## 7. Security-Sensitive Code Review

### Security Concern: Marketplace Identity Path Traversal

Location:

- `workflows/marketplace/client.py`
- `get_vsix_path()`
- `_artifact_name()`
- `_extension_dir()`
- `packages/analysis_planner/io.py`
- `write_trigger_file()`
- `executor/host.py`
- `install_extension_in_executor()`

Problem:

`publisher`, `name`, and `version` are used to construct filesystem paths. The request schemas currently enforce minimum length but not safe path characters.

Attack/failure scenario:

A crafted request uses `publisher="../outside"` or includes slashes/backslashes. Generated VSIX, extracted extension, trigger, or container paths may resolve outside the intended directory.

Impact: High.

Recommended mitigation:

Add shared identity validation for marketplace artifact components. Reject path separators, `..`, NUL, empty parts, and unexpected characters. Also verify resolved output paths remain under configured base directories.

### Security Concern: Unbounded VSIX Extraction

Location:

- `workflows/marketplace/client.py`
- `_extract_vsix_to_dir()`
- `download_and_extract_vsix()`

Problem:

ZIP member path traversal is checked, but archive size, decompressed size, and file count limits are not clearly enforced.

Attack/failure scenario:

A hostile VSIX contains a huge number of files or compressed data that expands massively, exhausting local disk or slowing the machine.

Impact: High.

Recommended mitigation:

Before extraction, enforce max compressed size, max total uncompressed size, max file count, and max single-file size. Fail closed with a clear report/job error.

### Security Concern: URI Trigger Shell Injection Inside Sandbox

Location:

- `executor/flows/playwright/entrypoint_triggers.py`
- `run_extra_triggers()`

Problem:

URI activation appears to type an `xdg-open '<uri>'` command into the VS Code terminal. If the URI contains a single quote or shell metacharacters, it can alter the shell command.

Attack/failure scenario:

A malicious manifest contributes a crafted URI activation value. The automation path gives it shell execution inside the executor container.

Impact: Medium to High.

Recommended mitigation:

Avoid terminal shell for URI triggers. Use a safe subprocess argument list inside the container, a VS Code command route, or strict URI validation plus `shlex.quote`.

### Security Concern: Docker Socket Mounted Into API Container

Location:

- `docker-compose.yml`
- `docker/api/Dockerfile`
- `docker/api/docker-entrypoint.sh`

Problem:

The API container mounts `/var/run/docker.sock`.

Attack/failure scenario:

If the API process is compromised, attacker-controlled code can control Docker on the host.

Impact: Critical if exposed beyond local trust boundary.

Recommended mitigation:

Keep API bound to local trusted use. Document this as a hard trust boundary. Do not expose the API to untrusted networks. Consider a startup warning if host binding is not localhost.

### Security Concern: noVNC and CDP Debug Surfaces

Location:

- `docker-compose.yml`
- `executor/container/start.sh`
- `executor/container/launch_vscode.sh`

Problem:

noVNC uses `-nopw`, and CDP is exposed on port 9222.

Attack/failure scenario:

Another local process or exposed network client can control the VS Code session.

Impact: Medium.

Recommended mitigation:

Bind to localhost only by default. Make exposed debugging ports explicit opt-in if feasible. At minimum, document that these are local diagnostic surfaces.

### Security Concern: VS Code Runs With `--no-sandbox`

Location:

- `executor/container/launch_vscode.sh`

Problem:

VS Code is launched with `--no-sandbox`.

Attack/failure scenario:

A malicious extension relies on the container as the only isolation boundary.

Impact: Medium.

Recommended mitigation:

This may be acceptable inside Docker, but the report and docs should state that Docker is the sandbox boundary. Keep container user non-root and minimize host mounts.

### Security Concern: Sensitive Data in Runtime Logs and Previews

Location:

- `executor/flows/playwright/runtime_capture/network.py`
- `executor/flows/playwright/runtime_capture/_shared.py`
- report output under `output/`

Problem:

Network body previews and filesystem paths may capture tokens, secrets, or local paths.

Attack/failure scenario:

An extension reads a token-like file and sends it over HTTP; the report stores part of the value.

Impact: Medium.

Recommended mitigation:

Hash bodies by default or redact obvious secret patterns. Keep optional previews short and clearly marked sensitive.

### Security Concern: Executor Excluded From Bandit

Location:

- `pyproject.toml`

Problem:

The most subprocess-heavy area is excluded from Bandit.

Attack/failure scenario:

Unsafe subprocess or shell behavior can land in executor code without automated static warning.

Impact: Medium.

Recommended mitigation:

Do not blindly enable Bandit for all executor code if noise is high. Add targeted security tests and narrow Bandit excludes instead.

## 8. Code Quality Review

| Area | Current State | Risk | Recommendation |
|---|---|---:|---|
| Function size | Several executor functions are long and orchestration-heavy | High | Extract pure helpers around mode dispatch, report finalization, and attempt recording |
| Naming | Generally clear and explicit | Low | Keep descriptive names; avoid generic "manager"/"handler" growth |
| Cohesion | Strong at top level, weaker inside Playwright monitor flow | Medium | Keep executor responsibilities split by lifecycle/capture/ledger/report |
| Coupling | Import-graph boundaries are good | Low | Preserve tests that enforce boundaries |
| Typing | Good contracts, but many report subfields use `dict[str, Any]` | Medium | Type unstable report substructures incrementally |
| Data modeling | Strong Pydantic contracts; runtime report object is too broad | High | Split report health/coverage/signal summary into submodels |
| Error handling | Better than average; report-first failure handling exists | Medium | Ensure every swallowed capture failure appears in report health |
| Input validation | Good Pydantic use, weak marketplace identity validation | High | Add safe identity/path validation |
| Dependency usage | Mostly reasonable | Low | Avoid new dependencies unless they remove real risk |
| Comments/docs | Some files have useful explanations; some service docstrings are noisy | Low | Prefer short comments around non-obvious failure semantics |
| Dead/clutter code | `docker/api 2` and local cache/build outputs appear in tree | Low | Clean only after verifying ownership |
| Test organization | Broad coverage but several huge test files | Medium | Split by behavior when touched |

## 9. Data Model and Event Schema Review

### Analysis runs

The project models analysis jobs through DB-backed job records and API schemas. This is appropriate because jobs need recovery and status reporting. The single active job invariant matches the product scope.

Risk: Low.

Recommendation: Keep the job model simple. Do not add a queue system.

### Extension metadata

Extension metadata is modeled through Pydantic catalog schemas and SQLAlchemy models. The unique `(publisher, name, version)` constraint is correct and must remain.

Risk: Low.

Recommendation: Add stricter validation for marketplace identity components before they are used in paths.

### Static findings

Static/detection findings are represented through `packages/analysis_contracts/detection/` and produced by `packages/analysis_engine/`.

Risk: Low.

Recommendation: Continue keeping detection contracts in `packages/`.

### Dynamic events

Dynamic events include network, file, process, UI blocker, scenario, and event-attempt records. The event model is good enough for a strong local security tool, but attribution and health logic are spread across several executor modules.

Risk: Medium.

Recommendation: Keep event names stable and add small typed models around high-churn event-attempt and health structures.

### Logs and traces

Logs are first-class citizens and report health attempts to distinguish capture failures from clean behavior. This is a strength.

Risk: Medium.

Recommendation: Add consistent run/job identifiers to executor-side log records where missing.

### Reports

The report contract is strong because it validates before write. The risk is size and mixed responsibility, not lack of schema.

Risk: High.

Recommendation: Do not create a generic event system. Instead, split large dict fields into typed submodels.

### Errors

The system is better than many projects at preserving failures in `automation_health`, `run_quality`, skipped scenarios, and report messages.

Risk: Medium.

Recommendation: Continue treating failed automation as inconclusive or failed, never clean.

## 10. Error Handling and Failure Modes

Strengths:

- Startup job recovery fails loudly on DB errors.
- Marketplace job failures are persisted.
- Executor report writing validates contracts.
- Dynamic automation can produce reports even when Playwright exits nonzero.
- Detection rule execution records rule errors instead of silently dropping them.
- Capture errors appear to feed into health/report fields.

Risks:

- Manifest parsing sometimes skips malformed data without a visible warning.
- Monitor capture strategies log and continue; this is acceptable only if final health clearly shows missing capture.
- `_docker_exec_allow_partial()` intentionally allows partial executor failure. That requires strict report-health validation downstream.
- Background thread exceptions are marked failed, but operational visibility depends on job status and logs.
- A failed dynamic run must never be interpreted as "no suspicious behavior."

Recommendations:

1. Preserve fail-closed semantics for sandbox setup, install, trigger-load, and report validation failures.
2. Add explicit report-health reasons for every capture source that fails.
3. Treat missing report, invalid report, failed trigger plan, and missing automation health as analysis failure.
4. Avoid broad `except Exception` blocks.
5. Ensure API responses distinguish:
   - clean extension
   - suspicious extension
   - inconclusive automation
   - failed sandbox
   - invalid package

## 11. Logging and Observability Review

Current state:

- The project has meaningful operational logs and report-level health fields.
- Runtime capture errors are not simply ignored.
- Reports include scenario traces, event attempts, skipped scenarios, and automation health.
- Network/file/process events carry attribution and evidence fields.

Strengths:

- Good direction for a defensive security tool.
- Report honesty is treated as part of the product, not an afterthought.
- Atomic report writes reduce partial-output ambiguity.

Gaps:

- Executor logs are still partly process-print oriented, which is acceptable locally but harder to correlate.
- Not every log line appears to carry a stable run/job/report identifier.
- Sensitive runtime data may be captured in local reports.
- Host actions and extension-owned actions are separated better than before, but attribution remains heuristic.

Recommendations:

1. Add a stable `run_id` or `job_id` to executor log records and final reports.
2. Keep host infrastructure events separate from target-extension events.
3. Redact or hash obvious secret-like body/path values.
4. Keep report health structured and machine-checkable.
5. Do not introduce distributed tracing or external observability stacks.

## 12. Testing Strategy Review

Current testing strengths:

- Architecture import tests enforce important boundaries.
- Marketplace extraction has ZipSlip-oriented tests.
- Detection rules and detection report invariants are tested.
- Executor behavior has substantial test coverage.
- Smoke tests exist for end-to-end behavior, though they are intentionally excluded from default pytest.

Current testing risks:

- Large test files reduce readability.
- Security-sensitive path validation is under-tested.
- Archive resource exhaustion is not clearly tested.
- URI trigger shell safety is not clearly tested.
- Some dynamic behavior depends on Docker/VS Code/Playwright state and must stay isolated from fast unit lanes.

Top 10 tests to add first:

1. Marketplace request rejects path separators, `..`, backslashes, and NUL in `publisher`, `name`, and `version`.
2. Generated VSIX, extension, trigger, and report paths must resolve under configured base directories.
3. VSIX extraction rejects excessive file count.
4. VSIX extraction rejects excessive decompressed size.
5. URI trigger containing quotes or shell metacharacters cannot alter the executed command.
6. Nonzero Playwright exit with a report results in failed or inconclusive automation health, not a clean result.
7. Fatal UI crash records failure reason, skipped scenarios, and degraded run quality.
8. Malformed `contributes` structures produce deterministic trigger-planning output instead of crashes or silent bad payloads.
9. Network body preview redacts or hashes obvious secret-looking values.
10. Detection engine does not emit clean/high-confidence verdicts when report health is failed or inconclusive.

Practical strategy:

- Keep fast unit tests for contracts, parser, planner, and detection.
- Keep Docker/Playwright smoke tests explicit and opt-in.
- Add focused security regression tests around path handling and archive extraction.
- Split very large tests only when touching them.

## 13. Dependency and Configuration Review

Dependencies:

- FastAPI, SQLAlchemy, Alembic, Pydantic, httpx, Playwright-related tooling, and Docker are justified.
- No obvious need for Redis, queues, service meshes, or distributed systems.
- The executor image installs necessary runtime capture tools such as `tcpdump`, `tshark`, `inotify-tools`, and `strace`.

Configuration concerns:

- API CORS defaults are loose for a local security tool.
- DB pool defaults are larger than needed for single-user local use.
- Docker socket mount is required by current architecture but security-critical.
- noVNC and CDP are exposed by default in Compose.
- `.env` exists locally; do not assume it is safe to mount broadly without checking contents.
- VS Code version pinning and harness checksum verification are good.

Recommendations:

1. Make local-only assumptions explicit in config names/docs.
2. Reduce DB pool defaults unless current tests require them.
3. Prefer localhost-bound debug surfaces.
4. Validate all configured filesystem paths at startup.
5. Keep dependency count minimal.

## 14. Maintainability Hotspots

| Hotspot | Why It Is Risky | Suggested Action | Priority |
|---|---|---|---|
| `workflows/marketplace/client.py` artifact paths | Raw identity fields influence filesystem paths | Add safe identity/path helper and tests | P0 |
| `packages/analysis_planner/io.py` trigger path | Trigger filename uses raw identity | Reuse same safe artifact helper | P0 |
| `executor/host.py` install paths | Container paths use raw identity values | Validate before constructing container paths | P0 |
| `executor/flows/playwright/entrypoint_runner.py` | Central orchestration point for dynamic analysis | Extract mode dispatch and finalization helpers | P1 |
| `executor/flows/playwright/monitor_lifecycle.py` | God object for capture, ledger, health, persistence | Split internals behind same facade | P1 |
| `executor/flows/playwright/monitor_types.py` | Giant mutable report object | Type high-churn report substructures | P1 |
| `executor/flows/playwright/stimulus_passes.py` | Complex layered activation state machine | Type attempt inputs/outcomes | P1 |
| `executor/flows/playwright/health_reconciliation.py` | Dense mutation of event attempts and health facts | Keep small, tested reconciliation helpers | P1 |
| `workflows/marketplace/trigger_service.py` | DB/manifest/planner/output bridge | Extract pure mapping helpers | P2 |
| `executor/flows/playwright/monitor.py` | Large compatibility facade | Freeze as re-export shim | P2 |
| Large executor/marketplace tests | Hard to use as behavior documentation | Split when touched | P2 |
| `docker/api 2` | Looks like abandoned workspace clutter | Verify and remove later | P3 |

## 15. Refactor Roadmap

### Immediate fixes

1. Goal: make artifact paths safe.
   Affected files/modules: `workflows/marketplace/client.py`, `packages/analysis_planner/io.py`, `executor/host.py`, request schemas.
   Expected benefit: closes path traversal class.
   Risk: Low.
   Suggested order: first.

2. Goal: add VSIX extraction limits.
   Affected files/modules: `workflows/marketplace/client.py`, marketplace tests.
   Expected benefit: prevents local resource exhaustion.
   Risk: Low to Medium.
   Suggested order: second.

3. Goal: remove shell-sensitive URI trigger behavior.
   Affected files/modules: `executor/flows/playwright/entrypoint_triggers.py`.
   Expected benefit: prevents sandbox shell injection through manifest-controlled URI values.
   Risk: Medium.
   Suggested order: third.

4. Goal: freeze compatibility facades.
   Affected files/modules: `executor/flows/playwright/monitor.py`, `executor/flows/playwright/attribution/__init__.py`.
   Expected benefit: prevents new logic from accumulating in shims.
   Risk: Low.
   Suggested order: fourth.

### Short-term refactors

1. Goal: reduce entrypoint complexity.
   Affected files/modules: `entrypoint_runner.py`.
   Expected benefit: safer dynamic-execution changes.
   Risk: Medium.
   Suggested order: after immediate security fixes.

2. Goal: split monitor internals.
   Affected files/modules: `monitor_lifecycle.py`, monitor helper modules.
   Expected benefit: clearer lifecycle, capture, ledger, and finalization ownership.
   Risk: Medium.
   Suggested order: after entrypoint cleanup.

3. Goal: type report health substructures.
   Affected files/modules: `packages/analysis_contracts/contracts.py`, `monitor_types.py`, report builder tests.
   Expected benefit: reduces raw dict drift.
   Risk: Medium.
   Suggested order: after monitor split.

4. Goal: split large tests by behavior.
   Affected files/modules: executor and marketplace tests.
   Expected benefit: easier regression work.
   Risk: Low.
   Suggested order: opportunistic.

### Medium-term improvements

1. Goal: improve event-attempt typing.
   Affected files/modules: `stimulus_passes.py`, `stimulus_attempts.py`, `packages/analysis_planner/`.
   Expected benefit: more deterministic layered activation behavior.
   Risk: Medium.

2. Goal: add explicit redaction policy.
   Affected files/modules: runtime capture and report builder.
   Expected benefit: safer local reports.
   Risk: Low to Medium.

3. Goal: strengthen negative fixtures.
   Affected files/modules: `tests/security/`, `tests/workflows/marketplace/`, `tests/executor/`.
   Expected benefit: catches hostile-package regressions.
   Risk: Low.

### Avoid for now

- Microservices.
- Message queues.
- Redis.
- Kubernetes.
- Service mesh.
- Distributed tracing stack.
- Plugin system.
- Generic event bus.
- Large dependency injection framework.
- Broad rewrite of executor.
- Replacing the current modular monolith with layered enterprise abstractions.

## 16. "Do Not Do This" List

- Do not split ExTrace into microservices.
- Do not introduce Kafka, RabbitMQ, Redis, or an event bus.
- Do not build a plugin framework for detection or trigger planning yet.
- Do not allow detection rules to import executor, workflow, UI, or storage code.
- Do not allow executor code to import `appcore` or workflow modules.
- Do not let Playwright automation directly contain detection rules.
- Do not let analyzer modules directly control Docker if `executor.control` exists as the boundary.
- Do not pass raw dictionaries through new code when a small typed model would clarify the contract.
- Do not hide subprocess, Docker, VS Code, or Playwright failures.
- Do not treat failed automation as a clean extension.
- Do not add abstractions with only hypothetical future use cases.
- Do not expose Docker socket, noVNC, or CDP to untrusted networks.
- Do not expand compatibility facades into real implementation files.
- Do not make `ActivationReport` the dumping ground for every new concept.
- Do not move business logic into routers.
- Do not let UI duplicate detection semantics.
- Do not remove report-health checks to make scans look cleaner.
- Do not optimize speed before correctness and observability.

## 17. Recommended Target Architecture

A realistic target architecture is still a modular monolith:

```text
Input Package / Marketplace Request
   ->
Ingestion / VSIX Download / Safe Extraction
   ->
Manifest Parser / Catalog Metadata
   ->
Trigger Planner
   ->
Executor Control Boundary
   ->
Docker Sandbox / VS Code / Playwright Automation
   ->
Runtime Event Capture
   ->
Report Builder / Health Reconciliation
   ->
Detection Engine
   ->
API/UI Report Presentation
```

Suggested modules and responsibilities:

- `appcore/api/`: settings, dependencies, API platform wiring.
- `appcore/storage/`: SQLAlchemy models and CRUD only.
- `appcore/contracts/`: API-facing request/response contracts.
- `workflows/extension_catalog/`: ingestion and manifest cataloging.
- `workflows/marketplace/`: marketplace download, analysis job orchestration, trigger preparation.
- `executor/control.py`: only workflow-to-executor boundary.
- `executor/host.py`: Docker command execution and container control.
- `executor/flows/playwright/`: VS Code automation, runtime capture, scenario execution, report creation.
- `packages/analysis_contracts/`: stable report, trigger, detection contracts.
- `packages/analysis_planner/`: deterministic trigger/scenario planning.
- `packages/analysis_engine/`: explainable detection rules and scoring.
- `ui/`: presentation only.

Allowed dependencies:

- `workflows/` may import `appcore/`, `packages/`, and `executor.control`.
- `executor/` may import `packages/`.
- `packages/` may import only framework-agnostic dependencies.
- `ui/` may call API contracts but should not own detection logic.

Forbidden dependencies:

- `packages/` must not import `appcore`, `workflows`, `executor`, or `ui`.
- `executor/` must not import `appcore` or `workflows`.
- Detection rules must not call Docker, Playwright, DB, or filesystem orchestration.
- Routers must not contain deep domain logic.
- UI must not reinterpret raw logs as findings independently from detection output.

## 18. Final Verdict

1. Is the codebase currently clean enough to continue building on?

Yes, but only if the next work tightens the executor/reporting hotspot instead of adding more behavior on top of it. The architecture is salvageable and mostly healthy.

1. What is the biggest architectural risk?

The Playwright monitor/report pipeline becoming the implicit center of all runtime, health, evidence, and detection semantics.

1. What is the biggest code quality risk?

The giant mutable activation report model plus raw `dict[str, Any]` substructures.

1. What is the biggest security engineering risk?

Unsanitized marketplace identity values influencing filesystem/container paths. The broader operational trust-boundary risk is the API's Docker socket access combined with exposed local debug surfaces.

1. What is the biggest overengineering risk?

Turning planner/report/health logic into a generic framework instead of keeping it as explicit, typed, local-first control flow.

1. What should be fixed before adding more features?

Safe identity/path validation, VSIX extraction limits, URI trigger shell safety, and clearer monitor/report ownership.

1. What should not be touched yet?

Do not replace the job model with a queue. Do not rewrite the executor. Do not remove compatibility facades casually. Do not change detection/report semantics without contract tests.

1. What is the next single best improvement?

Implement one shared safe artifact identity/path helper and use it everywhere `publisher`, `name`, and `version` become filenames, directories, report names, trigger files, or container paths.

Analysis scope:

- Files modified: none for the original review; this document was created afterward.
- DB schema changed: No.
- Tests added/updated: No.
- Tests run: No; the review was analysis-only.
- Assumption: assessment is based on the current dirty `week7` worktree and representative code inspection, not a full exhaustive audit.
