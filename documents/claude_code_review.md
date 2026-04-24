# ExTrace Codebase Quality & Architecture Report

`Generated: 2026-04-24`
`Reviewer: Claude (Opus 4.7) — analysis-only pass`

## 1. Executive Summary

ExTrace is, on the whole, a **competently engineered modular monolith** that has resisted most of the usual rot patterns you see in security tools at this maturity. The packages/workflows/executor/UI split is real, not cosmetic: it is enforced by AST-based architecture tests ([tests/architecture/test_import_graph.py](../tests/architecture/test_import_graph.py)). Detection rules are pure functions over typed Pydantic contracts. FastAPI routers stay thin. The Docker boundary is gated through a single `ExecutorControl` dataclass ([executor/control.py](../executor/control.py)). CRUD is channeled. There is no `shell=True` anywhere in production code. `except Exception` appears only in a docstring example and one seed script.

That said, there are **three concrete drift signals** that, left unattended, will become expensive:

1. **Executor-side detection leakage.** [signal_policy.py:52-485](../executor/flows/playwright/signal_policy.py) encodes signal categories, confidence thresholds (`0.82`, `0.78`, `0.84`), and attribution filters that belong in `packages/analysis_contracts/` or `packages/analysis_engine/`. Today a rule-threshold tweak requires redeploying the executor container.
2. **Playwright god-module cluster.** [monitor_lifecycle.py:1-834](../executor/flows/playwright/monitor_lifecycle.py) owns orchestration + capture coordination + three parallel log-parsing strategies + report finalization + scenario accounting. Methods like `stop()` (≈90 LoC, 4 nesting levels, three back-to-back try/except strategies at lines 250–289) are where this concentration is visible.
3. **Dual-import fragility.** Virtually every file under `executor/flows/playwright/` begins with a `try: from .X import …; except ImportError: from X import …` block so the same file works both as a package member and as a top-level module inside the container. This is silently covering for an unresolved packaging question and guarantees that mis-imports fail in the least visible way (wrong module loads, no error).

**Overengineering risks are low but present**: [packages/analysis_planner/registry.py](../packages/analysis_planner/registry.py) is 669 LoC of static capability/scenario config-as-Python; the attribution `__init__.py` re-exports 29 underscore-prefixed names as a preserved legacy API; the `_TriggerPayloadDraft` dataclass shadows the `TriggerPayload` Pydantic model during construction.

**Security posture is strong** for a local-first tool: zip-slip defense is explicit ([workflows/marketplace/client.py:144-170](../workflows/marketplace/client.py)), no `shell=True`, no bare subprocess strings, all subprocess calls use list-form with bandit `nosec` annotations, path containment via `resolve().relative_to()`, per-fixture tier hygiene (ADR 0004), and `make test-security-live` refuses to run under `CI=true`. Two non-critical gaps: no zip-bomb compression-ratio guard on VSIX extraction, and `signal_policy.py` does `sys.path.insert(0, …)` at import time.

**Architecture status: Mostly healthy with risks.**

Justification: The core architecture (packages/workflows/executor/UI separation, enforced by import-graph tests), data modeling (strict Pydantic, stable enums, verdict rollup), and security posture (Docker sandbox, zip-slip defenses, CRUD channeling, no shell injection) are production-grade. The risks are localized to the executor/playwright subtree — specifically the monitor/signal-policy cluster — and the planner registry. None of them require a rewrite. All are addressable with small, targeted refactors that tighten already-working seams.

---

## 2. Repository Structure Assessment

| Folder | Owns | Clear? | Overlap | Verdict |
|---|---|---|---|---|
| `main.py` | FastAPI app factory + single-worker guard | Yes | None | Keep. |
| `appcore/api/` | Pydantic settings, FastAPI deps | Yes | None | Keep. |
| `appcore/db/session.py` | SQLAlchemy 2.0 engine/session | Yes | None | Keep. |
| `appcore/storage/{crud,crud_ops,models,model_defs}/` | ORM models + CRUD facade | Yes | Minor — `crud.py` is a facade re-export; `crud_ops/` is where the real logic lives | Keep, but document the facade clearly. |
| `appcore/contracts/` | Shared request/response schemas (Pydantic) | Yes | None | Keep. |
| `workflows/extension_catalog/` | Manifest read + parse + catalog persistence + HTTP router | Yes | None | Keep. |
| `workflows/marketplace/` | VSIX download + job orchestration + analysis execution + report loading | Partial | `analysis_service.py` vs `analysis_execution.py` vs `job_service.py` responsibilities overlap around progress reporting and step state | Consider merging `analysis_service` + `analysis_execution` long-term. Not urgent. |
| `workflows/activation_reports/` | Read-only HTTP over on-disk activation reports | Yes | None | Keep. |
| `packages/analysis_contracts/` | Pydantic data contracts + enums + invariants | Yes | None | Strongest module in the repo. |
| `packages/analysis_engine/` | Pure detection rules + runner | Yes | None | Keep. |
| `packages/analysis_planner/` | Capability/scenario taxonomy + trigger payload construction | Yes, but **too broad** | `registry.py` mixes data, metadata, and indexes | Split registry into `capabilities.py`, `scenarios.py`, `coverage.py`. |
| `executor/control.py` + `host.py` | Host-side boundary to Docker | Yes | None | Cleanest seam in the repo. |
| `executor/container/` | Dockerfile + `start.sh` + `launch_vscode.sh` | Yes | None | Keep. |
| `executor/flows/playwright/` | In-container automation + runtime capture + monitor + attribution + signal policy | **No — too broad** | Monitor, signals, attribution, stimulus, scenarios, workspace-seeding all live at the same flat level (35+ files in one directory) | Split into subpackages: `monitor/`, `signals/`, `stimulus/`, `workspace/`. Attribution already split. |
| `executor/flows/playwright/runtime_capture/` | Network, filesystem, extension-host taps | Yes | None | Keep. |
| `executor/flows/playwright/attribution/` | Event annotation + evidence link construction | Yes | None | Good recent split. |
| `executor/flows/harness_extension/` | Not reviewed in depth; implied helper | Unknown | Unknown | Inspect before touching. |
| `tests/architecture/` | AST-based import-graph enforcement | Yes | None | Gold. |
| `tests/security/` | Detection rule validation + fixture hygiene + benign silence | Yes | None | Gold. |
| `tests/executor/`, `tests/platform/`, `tests/workflows/`, `tests/smoke/` | Layered test pyramid | Yes | None | Keep. |
| `extensions/malicious/` | T1 synthetic canaries | Yes (ADR 0004) | None | Keep. |
| `documents/` + `documents/adrs/` | Decision records + refactor status | Yes | Too many files — 20 top-level MD files signal organizational drift | Archive superseded docs. |
| `scripts/` | Demo acceptance + seed/test helpers | Yes | None | Keep. |
| `ui/src/` | Vite/React frontend | Not deep-reviewed | Unknown | Out of scope for this pass. |

**Call-outs:**

- **`executor/flows/playwright/` is too flat.** 45+ files at one level. Module prefix conventions (`monitor_*`, `stimulus_*`, `workspace_seed_*`, `health_*`, `entrypoint_*`) are a substitute for folders. This is the single most obvious architectural drift signal.
- **The `appcore/storage/crud.py` facade vs. `appcore/storage/crud_ops/` split is non-obvious.** A newcomer would not know which to open first.
- **`workflows/marketplace/analysis_service.py` + `analysis_execution.py` + `analysis_reports.py` + `analysis_errors.py`** is four files for what reads as one domain. Justifiable, but at the line between helpful split and over-splitting.

---

## 3. Main Execution Flow

Traced end-to-end:

1. **HTTP request** → [workflows/marketplace/router.py](../workflows/marketplace/router.py) receives `POST /analyze`.
2. **Job creation** → [workflows/marketplace/job_service.py](../workflows/marketplace/job_service.py) writes an `AnalysisJob` row via [appcore/storage/crud_ops/analysis_jobs.py](../appcore/storage/crud_ops/analysis_jobs.py) with a boot-ID stamp (survives restart).
3. **VSIX fetch + extract** → [workflows/marketplace/client.py:144-170](../workflows/marketplace/client.py) validates and zip-slip-safely extracts the VSIX into a partial dir then atomically renames.
4. **Manifest parse** → [workflows/extension_catalog/manifest_parser.py](../workflows/extension_catalog/manifest_parser.py) + `manifest_reader.py` produce typed views.
5. **Trigger planning** → `build_trigger_payload(db, request)` in `trigger_service.py` walks the capability/scenario taxonomy in [packages/analysis_planner/registry.py](../packages/analysis_planner/registry.py) and produces a `TriggerPayload` (Pydantic).
6. **Sandbox reset** → [workflows/marketplace/analysis_execution.py:86-104](../workflows/marketplace/analysis_execution.py) calls `ExecutorControl.reset_sandbox()` → [executor/host.py](../executor/host.py) → `docker exec` → [executor/flows/playwright/reset_state.py](../executor/flows/playwright/reset_state.py) (terminate VS Code, clean singleton locks, relaunch).
7. **Extension install** → `ExecutorControl.install_extension()` → `code --install-extension` inside container, with opportunistic reload-on-IPC-failure retry in [executor/host.py](../executor/host.py).
8. **Run automation** → `ExecutorControl.run_automation()` → `docker exec python3 /home/executor/flows/playwright/entrypoint.py --monitor ...` → [executor/flows/playwright/entrypoint_runner.py:main](../executor/flows/playwright/entrypoint_runner.py) (487 LoC) starts `ExtensionMonitor` (which spins network, filesystem, and extension-host taps), drives scenarios through `_run_scenario_sequence` in [automation.py](../executor/flows/playwright/automation.py), dismisses UI blockers, and calls back on page-reload via an `on_page_reloaded` hook.
9. **Monitor stop** → [monitor_lifecycle.py:stop](../executor/flows/playwright/monitor_lifecycle.py) runs three parallel activation-discovery strategies (exthost logs → Running Extensions UI → extension-host stdout), merges them, annotates events (via `attribution/`), and serializes `ActivationReport` to `/results/<name>.json`.
10. **Report load + validate** → [workflows/marketplace/analysis_reports.py](../workflows/marketplace/analysis_reports.py) reads JSON, validates against `ActivationReport` Pydantic schema (with legacy-verdict migration at [contracts.py:358-367](../packages/analysis_contracts/contracts.py)).
11. **Detection** → [packages/analysis_engine/runner.py:run_detection](../packages/analysis_engine/runner.py) iterates production rules, catches `(AttributeError, KeyError, TypeError, ValueError)` per rule, rolls up `Verdict` via [detection/rollup.py](../packages/analysis_contracts/detection/rollup.py), degrades health to `inconclusive` on rule errors (ADR 0003 §5).
12. **Serve report** → [workflows/activation_reports/router.py](../workflows/activation_reports/router.py) exposes the read-only file over HTTP with path-traversal guards (rejects `..`, `/`, `\\`).
13. **UI fetch** → React consumes the bundle.

**Boundary cleanliness**:

- Steps 1–3 (HTTP → job → VSIX) are **clean**. Routers stay thin; services own orchestration.
- Step 4 (parse) is **clean**. Manifest parsing is defensive and local.
- Step 5 (plan) is **clean** at the boundary, **messy internally** — the `_TriggerPayloadDraft` mutable dataclass is used through planning and only converted to the Pydantic `TriggerPayload` at finalization.
- Step 6–7 (sandbox reset + install) are **very clean**. `ExecutorControl` is a 63-line dataclass and is the only way workflows reach the sandbox.
- Step 8–9 (automation + monitor) is **the drift zone**. Detection-adjacent logic (signal policy, risk-signal scoring, confidence tiers) is computed *inside* the executor via `signal_policy.py`, not in `packages/`. The sandbox produces not only raw events but also pre-scored signals. The split is muddy.
- Step 11 (detection) is **clean**. Rules are pure and read an already-annotated `ActivationReport`.
- Step 12–13 (serve + UI) is **clean**.

---

## 4. Module Boundary Review

| Boundary | State | Risk | Evidence | Recommendation |
|---|---|---|---|---|
| Ingestion ↔ Static parsing | Clean split | Low | `manifest_reader.py` reads, `manifest_parser.py` parses; both pure | No change |
| Static ↔ Dynamic execution | Clean via `ExecutorControl` | Low | [executor/control.py](../executor/control.py) is the only workflow→sandbox entrypoint, enforced by `test_workflows_use_only_executor_control_boundary` | No change |
| Sandbox orchestration ↔ Detection | **Blurred** | **High** | [signal_policy.py](../executor/flows/playwright/signal_policy.py) computes risk signals with hardcoded confidence thresholds (lines 123–169), inside executor. Rules in `packages/analysis_engine/` consume a report that has *already* been partially judged by the executor. | Move signal construction into `packages/` and have executor emit only raw + attributed events. |
| Playwright automation ↔ Behavioral analysis | Blurred | Medium | `monitor_lifecycle.stop()` interleaves capture tear-down, log parsing, event merging, and report finalization in one 90-line method | Split `ExtensionMonitor` into `MonitorRuntime` (capture lifecycle) + `ReportAssembler` (merge + finalize) |
| Logging/tracing ↔ Detection | Clean | Low | `_log()` in `runtime_capture/_shared.py` is a single helper; detection rules don't log | No change |
| Backend/API/CLI ↔ Domain logic | Clean | Low | Routers only parse HTTP, call services, translate errors | No change |
| Reporting ↔ Raw event collection | Mixed | Medium | The `ActivationReport` is both the raw-event container and the annotated/summarized output; fields like `signal_summary`, `risk_signals`, `coverage_matrix` grow alongside `network_events`/`file_events` | Consider splitting into `RawActivationCapture` (events only) and `ActivationReport` (annotated). Non-urgent. |
| Infrastructure ↔ Domain | Clean | Low | SQLAlchemy/Pydantic scoped to `appcore/`; `packages/` has zero framework imports | No change |
| Host ↔ Container | Clean | Low | Host never imports from `executor/flows/*`; all crossings are via `docker exec` with list-form args | No change |

---

## 5. Spaghetti-Code Risk Analysis

### Issue: Detection logic embedded in executor

**Location**: [executor/flows/playwright/signal_policy.py](../executor/flows/playwright/signal_policy.py) (485 LoC), particularly `build_risk_signals()` (lines 52 onward).

**Problem**: The module owns hardcoded signal categories (`"background_sensitive_file_access"`, `"background_outbound_network"`), hardcoded confidence numbers (`0.82`, `0.78`, `0.84`, `0.70`), and attribution-status filtering (`"target_attributed"`, `"near_target_activation"`). It uses `importlib.import_module("packages.analysis_contracts.detection.enums")` after manually inserting the project root into `sys.path` (lines 31–37) to reach into the contracts package.

**Why it matters**: Every detection-tuning change now requires an executor container rebuild. Testing detection scoring in isolation is impossible because the scorer runs only inside the monitor lifecycle. The `sys.path` manipulation makes the import order fragile to layout changes.

**Risk level**: **High.** This is the single biggest architectural drift signal in the repo.

**Recommended fix**: Move signal-scoring into `packages/analysis_engine/signals/` and have the executor emit an `ActivationReport` with only raw + attributed events. Scoring happens post-report, alongside rules, in a unit-testable package.

---

### Issue: `monitor_lifecycle.py` god module

**Location**: [executor/flows/playwright/monitor_lifecycle.py](../executor/flows/playwright/monitor_lifecycle.py) (834 LoC).

**Problem**: Single class `ExtensionMonitor` owns: lifecycle (`__enter__`/`__exit__`/`start`/`stop`), capture coordination (network/fs/extension-host taps), three parallel log-parsing strategies (lines 250–289), scenario state accounting (`mark_trigger_plan_applied`, `record_failed_scenarios`, `record_execution_result`, `_finalize_running_scenarios`), report persistence (`_persist_report`), derived-state refresh (`_refresh_derived_report_state`), and activation-log appending.

The `stop()` method alone runs three back-to-back `try/except` blocks over three parsing strategies and calls `_persist_report(force=True)` four times.

**Why it matters**: Every change to scenario accounting, every new capture type, every new log-parsing strategy lands in the same file. Nothing is unit-testable in isolation — tests in [tests/executor/test_playwright_monitor_lifecycle.py](../tests/executor/test_playwright_monitor_lifecycle.py) largely mock the surrounding API.

**Risk level**: **High.**

**Recommended fix**: Split along the seams already implicit in the code: `MonitorRuntime` (capture start/stop), `ReportAssembler` (stop-phase log parsing + merging), `ScenarioAccountant` (scenario state). Keep `ExtensionMonitor` as a thin composition facade.

---

### Issue: Dual-import fallback `try: from .X ... except ImportError: from X ...`

**Location**: ~20 files across `executor/flows/playwright/` (e.g., [monitor_lifecycle.py:11-94](../executor/flows/playwright/monitor_lifecycle.py), [signal_policy.py:13-28](../executor/flows/playwright/signal_policy.py), [attribution/**init**.py:16-33](../executor/flows/playwright/attribution/__init__.py)).

**Problem**: Every module has to work in two import modes — (a) installed as a package from the repo root, (b) invoked from inside the container where `sys.path` starts at `/home/executor/flows/playwright/`. Fallback is silent `ImportError` catch.

**Why it matters**: If the relative import fails for a reason other than "we're in container mode" — e.g., a renamed module, a circular import — the top-level import is tried, succeeds against a *different* module with the same name, and the wrong code runs. No error at import time; failure manifests far downstream.

**Risk level**: **Medium.** Not actively breaking, but a latent foot-gun.

**Recommended fix**: Pick one mode. Either install the executor flows as a real package inside the container (`pip install -e .` in Dockerfile targeting `packages/` + `executor/`), or normalize the container entrypoint to set `PYTHONPATH` to the repo root. Then delete the fallback blocks.

---

### Issue: Three-strategy log parsing in `stop()` with divergent error handling

**Location**: [monitor_lifecycle.py:250-289](../executor/flows/playwright/monitor_lifecycle.py).

**Problem**: Three strategies (exthost logs, Running-Extensions UI, extension-host stdout) each wrapped in their own `try/except`, each persisting the report mid-flight, each catching a different combination of exception types.

**Why it matters**: Strategy A's failure mode (OSError on log read) is silently logged and the code moves on. Strategy B's UI scrape has an inner recovery press-Escape that itself can fail silently. Strategy C's OSError is logged only. There's no record in the output report of *which* strategies produced the activation evidence or *why* the ones that failed failed.

**Risk level**: **Medium.**

**Recommended fix**: Each strategy returns `(result, error)`; `stop()` composes them and records strategy-level status in the report (`report.activation_discovery_status = {...}`).

---

### Issue: `_TriggerPayloadDraft` mutable dataclass parallel to Pydantic `TriggerPayload`

**Location**: [packages/analysis_planner/selection.py:30-59](../packages/analysis_planner/selection.py), finalized via [coverage.py:123](../packages/analysis_planner/coverage.py).

**Problem**: Planning constructs a mutable `@dataclass` draft, mutates it across multiple functions, converts to Pydantic only at the last step. Between start and end, there is no type validation.

**Why it matters**: Anyone adding a field to `TriggerPayload` has to remember to add it to the draft too. Schema drift risk. Defeats half the point of using Pydantic.

**Risk level**: **Medium.**

**Recommended fix**: Use `TriggerPayload.model_construct()` for mid-flight mutation (skips validation but preserves typing), validate at finalization. Or use Pydantic throughout.

---

### Issue: Planner registry as code

**Location**: [packages/analysis_planner/registry.py](../packages/analysis_planner/registry.py) (669 LoC).

**Problem**: 26-item capability taxonomy, 3 parallel capability-support maps (global/official/heuristic), 15+ `ScenarioDefinition` tuples, pass-order/labels/descriptions dicts — all as Python literals.

**Why it matters**: Adding a scenario is a 4-location edit with no compile-time integrity check that all scenarios referenced by `EVENT_TYPE_TO_SCENARIOS` actually exist in `SCENARIO_REGISTRY`. It's a config file pretending to be code.

**Risk level**: **Medium.**

**Recommended fix**: Split into `capabilities.py`, `scenarios.py`, `event_scenario_index.py`. Add a module-level consistency check (assert all referenced scenario names exist) that runs at import — turns a latent bug into an import-time failure.

---

### Issue: Silent `verdict → signal_summary` legacy migration

**Location**: [packages/analysis_contracts/contracts.py:358-367](../packages/analysis_contracts/contracts.py).

**Problem**: `@model_validator(mode="before")` silently renames the old field. No deprecation warning, no `migrated_from_legacy` marker, no `schema_version` field on `ActivationReport` (note: `DetectionReport` has `schema_version: Literal["1"]` — the drift is one-sided).

**Why it matters**: Callers emitting the old shape never learn. When the field is eventually removed, pre-existing on-disk reports will silently fail.

**Risk level**: **Low–Medium.**

**Recommended fix**: Add `schema_version: Literal["1"] = "1"` to `ActivationReport`. Emit a one-time `warnings.warn(DeprecationWarning)` inside the validator when it fires.

---

## 6. Overengineering Risk Analysis

### Issue: Attribution facade preserving 29 underscore-prefixed names

**Location**: [executor/flows/playwright/attribution/**init**.py:113-143](../executor/flows/playwright/attribution/__init__.py).

**Problem**: The recent `monitor_attribution.py` → `attribution/` split explicitly preserves 29 `_`-prefixed names as public-of-package exports. CLAUDE.md notes this was intentional to avoid touching three callers.

**Why it is overengineered**: Preserving a large underscore-prefixed private API across a refactor indicates the split wasn't committed to. It's a halfway house.

**Simpler alternative**: Either make the exports public (drop the leading `_` in the facade) or rename call sites. 3 callers is a one-commit change.

**Risk level**: Low.

---

### Issue: Parallel `ExecutorControl` + `default_executor_control` + DI injection

**Location**: [executor/control.py](../executor/control.py) + usage in `workflows/marketplace/analysis_execution.py`.

**Problem**: `ExecutorControl` is a `@dataclass(slots=True)` with no fields. It exists purely to be a method-holder that can be swapped out for tests. A module-level `default_executor_control` is provided for the non-test path.

**Why it is overengineered** (marginally): The class has no state. It could be a module of free functions, and tests could patch the module. The DI ceremony adds one indirection for zero current behavior variation.

**Simpler alternative**: Keep it — the dataclass pattern is cheap and documents the boundary. This is the one place I'd say **do NOT simplify.** The boundary value is worth the 60 lines.

**Risk level**: Low — noted here only to explicitly defend it.

---

### Issue: `workflows/marketplace/` split into 5 files for one workflow

**Location**: `analysis_service.py` + `analysis_execution.py` + `analysis_reports.py` + `analysis_errors.py` + `job_service.py` + `trigger_service.py`.

**Problem**: The marketplace analysis is one orchestration pipeline split across six files, with overlapping progress-reporter plumbing.

**Why it is overengineered**: Reading end-to-end requires cross-file hopping. `StepReporter` is defined in one, step enum lives in `appcore/contracts/schema_defs/`, and step-mutation helpers live in `job_service.py`.

**Simpler alternative**: Fold `analysis_execution.py` back into `analysis_service.py`. Keep `analysis_reports.py` separate (different concern: read-only report loading). Keep `analysis_errors.py`.

**Risk level**: Low. Not urgent; the current split isn't broken.

---

### Issue: Planner `registry.py` 669 LoC as code

Already noted in §5. Overengineering angle: the Python file supports programmatic manipulation, but nothing in the codebase actually manipulates it programmatically — every consumer reads static values. YAML would be faithful to its actual role.

**Risk level**: Low–Medium.

---

## 7. Security-Sensitive Code Review

### Security Concern: No zip-bomb ratio guard on VSIX extraction

**Location**: [workflows/marketplace/client.py:144-170](../workflows/marketplace/client.py) — `_extract_vsix_to_dir`.

**Problem**: Zip-slip is defended (`startswith("extension/")`, `".." in parts` rejection, `resolve().relative_to()` containment). However, there's no check on compressed-vs-uncompressed size ratio and no per-entry size cap. A hostile VSIX with a 10KB compressed / 10GB uncompressed member will OOM the extraction process.

**Attack/failure scenario**: Attacker uploads or serves a malicious VSIX via a spoofed marketplace URL (or local flow accepts a file). Extraction fills disk / RAM, taking out the host (which is the operator's machine).

**Impact**: **Medium.** Local DoS on the operator's host. Not privilege escalation.

**Recommended mitigation**: Iterate `zf.infolist()`; abort if cumulative uncompressed size exceeds a ceiling (e.g., 256 MB) or any single file exceeds 64 MB. These are small, pragmatic caps.

---

### Security Concern: `sys.path` manipulation inside executor runtime

**Location**: [signal_policy.py:31-37](../executor/flows/playwright/signal_policy.py), also [report_builder.py](../executor/flows/playwright/report_builder.py).

**Problem**: `sys.path.insert(0, _PROJECT_ROOT)` at import time, followed by `importlib.import_module(...)` to reach `packages.analysis_contracts.detection.enums`.

**Attack/failure scenario**: If the repo layout changes or if an attacker-controlled path shadows `packages/` on the Python path (less likely given this is inside the container), a different `quantize_confidence` loads. Detection scoring is compromised silently.

**Impact**: **Low–Medium.** In the current sandbox layout this is safe. It is a latent fragility, not an active vulnerability.

**Recommended mitigation**: Install `packages/` as a real installed package inside the container; remove `sys.path.insert`.

---

### Security Concern: `find_exthost_logs()` / extension-host file globbing on untrusted paths

**Location**: [executor/flows/playwright/monitor_sources.py](../executor/flows/playwright/monitor_sources.py) and runtime_capture/extension_host.py.

**Problem**: These modules glob VS Code log directories inside the container. Log directory paths themselves are trusted (they come from VS Code, which has been installed by Dockerfile), but log *contents* are parsed and incorporated into `report.extension_host_output` and log-stream entries.

**Attack/failure scenario**: A hostile extension writes crafted log lines that, when concatenated into the report, could inflate output size (`extension_host_output_lines`) or inject misleading activation strings. The parser heuristically looks for `"activated"` substrings — a hostile extension could log fake activations attributing benign behavior to other extensions.

**Impact**: **Low.** Confuses the analyst; does not escape the sandbox. The Docker boundary is the real control.

**Recommended mitigation**: Cap `extension_host_output` length on read (sample + tail). Already hinted by `extension_host_output_lines` field. Treat activation parsing as best-effort, not authoritative, and rely on attribution-status for high-confidence actor identification.

---

### Security Concern: Subprocess invocations rely on PATH resolution

**Location**:

- [editor.py:38-41](../executor/flows/playwright/editor.py) — `xdotool`
- [monitor_runtime.py:202](../executor/flows/playwright/monitor_runtime.py) — `ps`
- [runtime_capture/network.py:268](../executor/flows/playwright/runtime_capture/network.py) — `tshark`
- [runtime_capture/filesystem.py:203](../executor/flows/playwright/runtime_capture/filesystem.py) — `inotifywait`
- [runtime_capture/extension_host.py:411](../executor/flows/playwright/runtime_capture/extension_host.py) — likely `tail`

**Problem**: All use list-form args (no shell injection risk), but rely on `PATH` to locate binaries. `nosec B607` annotations explicitly acknowledge this.

**Attack/failure scenario**: Inside the Docker container, a hostile extension with write access to a `PATH`-early directory could shadow `tshark`/`ps` with a trojan that emits fake events or spawns a reverse shell.

**Impact**: **Low** in current setup (hostile extensions run as a different user without `PATH` write on the critical dirs) but depends on container user/umask. Worth verifying the Dockerfile user model.

**Recommended mitigation**: Use absolute paths (`/usr/bin/ps`, `/usr/bin/tshark`). Small change, removes the PATH dependency, keeps `nosec` unnecessary.

---

### Security Concern: `execution/flows/playwright/editor.py` sends keyboard input to X server

**Location**: [editor.py:38-41](../executor/flows/playwright/editor.py) uses `xdotool key ctrl+a`, `xdotool type --delay 30 <filename>`, `xdotool key Return` with `check=True`.

**Problem**: Filename passed to `xdotool type --delay 30` is user-controlled only via scenario definitions inside the repo. Not user-exposed. But if a future scenario ingests an extension-provided value, `xdotool type` would inject whatever it receives into the focused window.

**Attack/failure scenario**: Hypothetical, not actively exploitable today.

**Impact**: Low today. Worth flagging so it isn't done in future.

**Recommended mitigation**: Document that `xdotool type` input must be from trusted (in-repo) sources only. Add a type-check / literal wrapper if any extension-provided string ever reaches this call.

---

### Security Concern: `.env` present in repo

**Location**: [.env](../.env) (955 bytes, listed in `ls -la`).

**Problem**: A `.env` file is present alongside `.env.example`. Cannot confirm contents without reading, but the presence of a committed `.env` is a red flag.

**Attack/failure scenario**: If committed to git, secrets leak. If only present locally (gitignored), this is fine.

**Impact**: Depends on git status.

**Recommended mitigation**: Verify `.env` is in `.gitignore`. Your `.gitignore` exists and is 752 bytes — spot-check it. If secrets are in `.env`, treat as already compromised and rotate.

---

### Security Concern: Activation-report filename validation uses substring, not regex

**Location**: [workflows/activation_reports/router.py:232,251](../workflows/activation_reports/router.py).

**Problem**: The router rejects `..`, `/`, `\\` and validates a filename pattern. Worth double-checking the pattern is anchored.

**Attack/failure scenario**: If the pattern matches `activation_report.json.weird`, a hostile symlink inside the reports directory could be followed.

**Impact**: **Low** — reports are local-only; the reports dir is under tool control.

**Recommended mitigation**: Use a strict regex (`^activation_report[0-9_-]*\.json$`) and resolve + containment-check like the VSIX extractor.

---

### Security posture summary

| Area | Status |
|---|---|
| Shell injection | **Clean** — no `shell=True`, no string concatenation, list-form everywhere |
| Path traversal — VSIX extraction | **Defended** |
| Path traversal — activation-report serving | **Defended** |
| Zip bomb | **Not defended** — LOW priority gap |
| Subprocess binary PATH | **Relies on PATH** — LOW priority gap |
| CRUD channeling | **Enforced** |
| Broad exception handling | **Only in docstring + seed script** |
| Sandbox boundary | **Explicit** via `ExecutorControl` + import-graph tests |
| Secret handling | `.env` present — **verify gitignore** |

---

## 8. Code Quality Review

| Area | Current State | Risk | Recommendation |
|---|---|---|---|
| Function size | Most functions under 60 LoC. Outliers: `build_risk_signals` (~200 LoC), `ExtensionMonitor.stop()` (~90 LoC), `entrypoint_runner.main()` (280 LoC per sub-agent) | Medium | Split the top 5 offenders; no project-wide line-limit enforcement needed |
| Naming | Generally clear. `monitor_*` prefix convention substitutes for directory structure | Low | Promote prefixes to subpackages |
| Cohesion | High within packages/; moderate in workflows/; low in executor/flows/playwright/ monitor cluster | Medium | Split monitor cluster |
| Coupling | Packages isolated, workflows bounded, executor has sys.path hacks reaching into packages | Medium | Install `packages/` into container; remove `sys.path.insert` |
| Typing | Pervasive type hints; Pydantic v2 at boundaries; `mypy` clean per CLAUDE.md | Low | Keep. Consider strict mode for packages/ |
| Data modeling | Strict Pydantic with `extra="forbid"` at boundaries; draft dataclasses in planner only | Low–Medium | Replace `_TriggerPayloadDraft` with `TriggerPayload.model_construct()` |
| Error handling | Typed exception catches everywhere; no bare `except Exception` in production | Low | Keep |
| Input validation | Manifest parser is defensive; marketplace client validates via Pydantic; zip-slip enforced | Low | Add zip-bomb guard |
| Dependency usage | 7 production deps, 8 dev — minimal | Low | Keep |
| Comments | CLAUDE.md notes this is a "Turkish dev notes" project in places; production comment density looks healthy | Low | Keep |
| Dead code | Not systematically audited, but `monitor.py` is a re-export shim (14 LoC), and the attribution facade preserves 29 legacy underscore names | Low | Trim after confidence in the split |
| Consistency | ImportError fallback pattern applied consistently across ~20 files (consistent, but consistently wrong) | Medium | Eliminate the pattern; do not propagate |
| Docstrings | Good at public APIs; executor helpers are lighter but reasonable | Low | Keep |
| Magic constants | Confidence thresholds scattered in signal_policy.py | Medium | Centralize in `packages/analysis_contracts/detection/thresholds.py` |

---

## 9. Data Model and Event Schema Review

**What is typed vs. untyped:**

- `ActivationReport` (350+ fields) — Pydantic, strict. ✅
- `DetectionReport`, `DetectionFinding`, `RuleExecutionRecord`, enums — Pydantic/StrEnum, strict, with `schema_version: Literal["1"]`. ✅
- `EvidenceEvent` — Pydantic, but `raw_context: dict[str, Any]` is untyped. Rules do `event.raw_context.get("event_type", "")` — safe fallback but unvalidated. ⚠️
- `TriggerPayload` — Pydantic; the intermediate `_TriggerPayloadDraft` is a mutable dataclass. ⚠️
- `automation_health` on `ActivationReport` — *a raw dict* on the way in, coerced to `AutomationHealthStatus` (Pydantic) only at [runner.py:_coerce_automation_health](../packages/analysis_engine/runner.py) — defensive but indicates upstream emits unvalidated shapes. ⚠️
- `coverage_matrix`, `coverage_tracks`, `official_event_coverage`, `heuristic_workflow_coverage` — all `dict[str, Any]` on `ActivationReport`. ⚠️

**Are schemas stable?** Yes — with the one exception of the `verdict` → `signal_summary` rename, handled by an opaque validator.

**Are events normalized?** Yes — `FileEvent`, `NetworkEvent`, `ProcessEvent` are Pydantic models, attribution-status is a typed field.

**Timestamps/run IDs/correlation IDs:** Present and consistent. `event_id` is stringly assigned (`file-{index:04d}`), not a ULID on the event itself. `DetectionFinding.id` is ULID. Synthetic event IDs (A3 typosquat creates `identity:{identifier}`) point to non-existent events — caught by `report_invariants.py` but not prevented at construction.

**Recommendations (all small):**

1. Type `raw_context` per event type (e.g., `FileRawContext`, `NetworkRawContext`) instead of `dict[str, Any]`. Can be done incrementally.
2. Add `schema_version: Literal["1"] = "1"` to `ActivationReport`. Makes the migration explicit.
3. Type `automation_health` on `ActivationReport` as `AutomationHealthStatus | dict[str, Any]` so the validator is visible in the schema, not hidden in the runner.
4. Consider typing `coverage_*` fields as Pydantic models rather than `dict[str, Any]`. The planner already has this data internally.

**What NOT to do:**

- Do not introduce a "universal event" model that unifies file/network/process. Keep per-type models.
- Do not add a schema registry / migration framework. Two validator lines are enough.

---

## 10. Error Handling and Failure Modes

**What's handled well:**

- **Subprocess failures**: Specific exception classes caught (`subprocess.CalledProcessError`, `subprocess.TimeoutExpired`, `OSError`). No blanket.
- **Docker failures**: `ExecutorError` raised from host.py with rc + output captured. Install failures surface stderr tail (500 chars) via `install_failure_message()` — good operator experience.
- **VS Code launch failures**: Handled via `reset_state.py` orchestration with explicit SIGTERM → grace → SIGKILL fallback.
- **Playwright failures**: `PlaywrightError` caught distinctly from `RuntimeError` and `ValueError`. Fatal UI crashes classified via `is_fatal_ui_error` and converted into `ScenarioTrace.failure_reason_code = "fatal_ui_crash"`; automation health degrades to `inconclusive` per ADR 0003 §5.
- **Timeout failures**: Per-step timeouts in monitoring heartbeat; `subprocess.TimeoutExpired` caught.
- **Malformed package files**: `PackageJsonReadError` custom exception; manifest_reader skips unreadable files.
- **Missing dependencies**: Not applicable (single-process app).
- **Invalid paths**: Guarded in activation_reports router; resolve+relative-to in VSIX extraction.
- **Partial analysis results**: ADR 0003's "error dominance" rule: any `RuleExecutionStatus.ERROR` degrades health to `inconclusive` before verdict rollup. ✅
- **Rule evaluation errors**: `runner.py:25` caps catch to `(AttributeError, KeyError, TypeError, ValueError)` — good narrow list.

**What's not handled well:**

- **Three-strategy log parsing** in `stop()` swallows per-strategy failures silently — no structured record of which strategies failed or why (only `_log()` lines).
- **Fallback imports** silently switch to a different module in container mode (§5).
- **`aborted_after_fatal_ui_crash` skipped scenarios** — actually this is now handled (per CLAUDE.md post-W7 continuation #3).

**Failure distinguishability:**

- Can a failed dynamic run be distinguished from a clean extension? **Yes** — `automation_health.status = "inconclusive"` is the signal. Verdict rollup explicitly refuses to emit `MALICIOUS` without a production rule (runner.py:149-158). Good.
- Is the operator alerted? Install failure tail exposure is excellent; monitoring heartbeat at 30s interval is reasonable.

**Recommendations:**

1. Add `report.activation_discovery_strategies: dict[str, str]` capturing each strategy's status (`ok` / `failed: <reason>` / `skipped`). Makes invisible failures visible without adding logging.
2. Eliminate dual-import fallback to remove silent-switch risk.

---

## 11. Logging and Observability Review

**Current state:**

- Logging uses `logging.getLogger(__name__)` in workflows (structured API-side).
- Executor uses a custom `_log()` helper (runtime_capture/_shared.py) that writes to stdout — captured by `docker exec`.
- Run correlation via `report_path` name (e.g., `/results/analysis_<publisher>_<name>_<version>.json`) — doubles as run ID.
- Events carry `event_id` (zero-padded sequence: `file-0001`, `network-0002`) — correlated within a report but not globally.
- Evidence bundles link event IDs → findings → scenarios.
- Discovery-log de-duplication is in place (per CLAUDE.md post-W7 continuation #6 — `_LAST_EXTHOST_LOG_COUNT` module-level guard).

**Strengths:**

- Host actions and extension actions are distinguishable via `attribution_status` (target_attributed / near_target_activation / competing_candidate / etc.) — the key property for evidence preservation.
- Rate-limited discovery logs keep scenario-progress output readable during `make sim-all`.
- Install-failure tail in job step messages gives operators diagnostic information.

**Weaknesses:**

- Two parallel log channels: Python `logging` (workflows) and `_log()` stdout helper (executor). No unified format.
- No structured JSON log lane — all log lines are freeform strings. Debugging a report means scrolling through stdout.
- No explicit secret redaction. If an extension's `.env` is read as part of capture, sensitive values could end up in `report.file_events.content_sample` (not verified — would require reading `filesystem.py`).

**Recommendations (small, local-first):**

1. Settle on one logging helper. Either move `_log()` to `logging.getLogger("extrace.executor")` with a dedicated handler, or keep `_log()` but wrap it as a proper logger. Two is one too many.
2. Add a `redact_secrets()` pass on any captured content samples before they enter `ActivationReport`. Regex for AWS keys, `Bearer`, `-----BEGIN`, common API-key prefixes. Cheap; high value if an extension reads an operator's `~/.aws/credentials`.
3. No need for JSON logs yet. No need for OpenTelemetry. No need for a trace store. The `report_path` is the run ID; events carry their own IDs. That is sufficient.

---

## 12. Testing Strategy Review

**Layers present and real:**

- Architecture (import-graph) — `tests/architecture/test_import_graph.py`, 3 tests, AST-enforced. ✅
- Unit — `tests/platform/`, mocked DB via `client` fixture. ✅
- Integration — `tests/workflows/`, `tests/platform/` with `requires_db`. ✅
- Executor — `tests/executor/` (16 files), mostly mocked Playwright API. ✅
- Security — `tests/security/` (6 files + `rules/` subdir): fixture hygiene, rule coverage, benign silence, invariants, canary end-to-end. ✅
- Smoke — `tests/smoke/`, `runtime_client` fixture, `@pytest.mark.smoke`. ✅

**What's strong:**

- Import-graph tests fail fast on boundary violations. Gold.
- `test_benign_silence.py` runs benign extensions (ms-python.python) against rules to prove zero false positives. Rare and valuable.
- `test_fixture_hygiene.py` checks LABEL.yaml manifests per ADR 0004 — tier discipline enforced.
- `test_rule_coverage.py` asserts every adversary class A1/A2/A4/A6 has a fixture that fires and each fixture has ≥1 detection contract.
- Rule tests (`tests/security/rules/test_a*.py`) exercise rules with synthetic reports.
- `make test-security-live` refuses under `CI=true` (ADR 0004).
- Demo acceptance script (`scripts/demo_acceptance.py`) provides end-to-end confidence.

**Gaps:**

- **Tests against the dual-import fallback**. Container-mode imports are never exercised by CI because tests run from the repo root. You could break the fallback branch and only discover it during `make exec-up`.
- **`signal_policy.py` is tested** (`tests/executor/test_signal_policy.py`) but the tests mock the import cascade. Move signal policy into `packages/` and the tests become cheaper and more honest.
- **Zip-bomb input test** is missing from `tests/workflows/marketplace/`.
- **Concurrency/race tests on `reset_state.py`** — SingletonLock cleanup is a recent fix; a test that simulates a stale lock would regression-prevent.
- **`ActivationReport` schema round-trip** is partially covered (`test_activation_report_accepts_legacy_verdict_field`). Extend: round-trip for each adversary-class fixture.
- **Benign-silence coverage** is present (`test_benign_silence.py`) but only for one extension; widening to 5–10 popular extensions catches over-firing early.

**Top 10 tests to add first:**

1. **Container import-mode test** — `tests/architecture/test_container_imports.py` — runs `python -m compileall executor/flows/playwright/` with `PYTHONPATH=executor/flows/playwright` and asserts every module imports clean. Module: architecture. Why: silent module-swap is a latent bug.
2. **Zip-bomb rejection test** — `tests/workflows/marketplace/test_vsix_extraction.py::test_rejects_high_compression_ratio`. Module: marketplace. Why: local DoS risk.
3. **Zip-bomb per-file-size test** — same module, `test_rejects_oversized_member`. Same reason.
4. **Signal policy extraction test** — after refactor, unit-test signal construction in `packages/` with handcrafted `ActivationReport` fixtures. Module: analysis_engine. Why: detection tuning needs isolation.
5. **`stop()` strategy-record test** — once §10 recommendation lands, assert `report.activation_discovery_strategies` reflects each strategy's status on synthetic failures. Module: executor. Why: failure visibility.
6. **Stale singleton-lock regression test** — `tests/executor/test_reset_state.py::test_recovers_from_stale_singleton_lock`. Module: executor. Why: the fix is recent; regression-prevent it.
7. **`.env` gitignore test** — `tests/architecture/test_secrets_hygiene.py::test_env_file_is_gitignored`. Module: architecture. Why: trivial, prevents accidental secret commit.
8. **Benign-silence expansion** — add 5 popular extensions (prettier, eslint, python, gitlens, copilot-stub) to `test_benign_silence.py`. Module: security. Why: false-positive risk is proportional to scope.
9. **Path-traversal test on activation-report router** — `tests/workflows/activation_reports/test_router.py::test_rejects_encoded_traversal` with `%2e%2e%2f`. Module: activation_reports. Why: basic web hardening.
10. **Schema-version migration emitter test** — after recommendation lands, assert a `DeprecationWarning` fires when a legacy `verdict`-field report is loaded. Module: contracts. Why: makes the silent migration audible.

---

## 13. Dependency and Configuration Review

**Production dependencies:**

```text
fastapi, uvicorn[standard], sqlalchemy (2.0), alembic,
psycopg2-binary, pydantic (v2), pydantic-settings, python-dotenv
```

**Assessment:**

- **Minimal.** No bloat, no transitive-dependency nightmare, no surprising inclusion.
- **SQLAlchemy 2.0-only** pinning is correct per AGENTS.md.
- **psycopg2-binary** is fine for local-first; no `psycopg2` source build needed.
- **No ORM wrapper frameworks** (no SQLModel, no Tortoise, no Pony).
- **No API client frameworks** beyond httpx (via FastAPI's test client).
- **Playwright + tshark + xdotool + inotify** implicit in the executor container — docker-compose and Dockerfile concerns, not runtime deps.

**Dev dependencies:**

- ruff, mypy, pytest, pytest-cov, pytest-asyncio, httpx, pre-commit, bandit. Standard stack. Keep.

**Configuration layering:**

- Pydantic `BaseSettings` subclasses (`DatabaseSettings`, `APISettings`, `ProjectSettings`, `ExecutorSettings`).
- `.env.example` documents 114 env vars, grouped by prefix.
- Docker-compose injects into containers.
- `conftest.py` has a localhost fallback for `DATABASE_URL`.

**Strengths:**

- Single source of truth (Pydantic settings).
- `.env.example` is documentation.
- Explicit "internal use only, no auth" warning in `.env.example`.
- `settings.api.WORKERS != 1` raises at startup (`validate_runtime_settings` in main.py) — fail-fast on misconfig.

**Weaknesses:**

- `.env` file present in repo. Verify gitignore.
- Some paths in executor container are hardcoded (`/home/executor/flows/playwright/...`) but these are container-internal, so fine.
- Magic confidence numbers in `signal_policy.py` are not part of the config system.

**Recommendations:**

1. Verify `.env` in `.gitignore`.
2. When extracting signal policy, move thresholds into a single Python dict keyed by signal category. Do not add YAML.
3. No framework change needed. Pydantic settings is sufficient.

---

## 14. Maintainability Hotspots

| Hotspot | Why It Is Risky | Suggested Action | Priority |
|---|---|---|---|
| [executor/flows/playwright/signal_policy.py](../executor/flows/playwright/signal_policy.py) | Detection scoring inside sandbox; sys.path hack; 485 LoC | Move to `packages/analysis_engine/signals/` | **P0** |
| [executor/flows/playwright/monitor_lifecycle.py](../executor/flows/playwright/monitor_lifecycle.py) | 834 LoC god module; 5+ responsibilities | Split into `MonitorRuntime` / `ReportAssembler` / `ScenarioAccountant` | **P1** |
| Dual-import `try/except ImportError` pattern across ~20 executor files | Silent module shadowing risk | Install `packages/` into container; remove fallbacks | **P1** |
| [packages/analysis_planner/registry.py](../packages/analysis_planner/registry.py) | 669 LoC of config-as-code, no consistency check | Split + add import-time consistency assertion | **P2** |
| `executor/flows/playwright/` directory (45+ files flat) | Visual/cognitive overload; prefix-as-folder | Introduce `monitor/`, `signals/`, `stimulus/`, `workspace/` subpackages | **P2** |
| [executor/flows/playwright/attribution/**init**.py](../executor/flows/playwright/attribution/__init__.py) | 29 underscore-prefixed re-exports preserved for legacy callers | Rename at callsites; drop underscores in public facade | **P2** |
| [packages/analysis_contracts/contracts.py](../packages/analysis_contracts/contracts.py) `_migrate_legacy_verdict` | Silent migration without schema_version or deprecation warning | Add `schema_version` field + one-time warning | **P2** |
| `_TriggerPayloadDraft` in `packages/analysis_planner/selection.py` | Mutable dataclass parallel to Pydantic payload | Use `model_construct()` mid-flight | **P2** |
| `stop()` method in `monitor_lifecycle.py` | 3 strategies, silent failure modes, 4 persist calls | Record per-strategy status; extract helper methods | **P1** |
| `workflows/marketplace/client.py::_extract_vsix_to_dir` | No zip-bomb guard | Add cumulative + per-member size caps | **P1** (security) |
| `workflows/marketplace/{analysis_service, analysis_execution, analysis_reports, analysis_errors, job_service, trigger_service}` | Six files for one workflow | Merge `service` + `execution` long-term | **P3** |
| `appcore/storage/crud.py` facade vs. `crud_ops/*` | Indirection without discoverability | Document in AGENTS.md or rename facade to `__init__.py` re-exports | **P3** |
| `documents/` top-level with 20 MD files | Documentation drift | Archive superseded docs into `documents/archive/` | **P3** |

---

## 15. Refactor Roadmap

### Immediate fixes (low risk, high-hygiene)

1. **Verify `.env` is gitignored.** Goal: prevent secret leak. Affected: `.gitignore`. Benefit: security. Risk: none. Order: first, 30 seconds of work.
2. **Add zip-bomb guards to VSIX extraction.** Goal: prevent local DoS. Affected: [workflows/marketplace/client.py](../workflows/marketplace/client.py). Benefit: operator host stability. Risk: very low. Order: second.
3. **Add `schema_version` to `ActivationReport` + `DeprecationWarning` in `_migrate_legacy_verdict`.** Goal: make silent migration observable. Affected: [packages/analysis_contracts/contracts.py](../packages/analysis_contracts/contracts.py). Benefit: future-proof the schema. Risk: none. Order: third.
4. **Replace `sys.path.insert` in `signal_policy.py` and `report_builder.py` with a proper import** (once container packaging is resolved — or accept as a stopgap note). Goal: fragility reduction. Affected: two files. Risk: low, but depends on container layout. Order: before the big refactor in §short-term.

### Short-term refactors (boundary-improving, pre-feature work)

1. **Resolve container vs. package import mode** — pick one. Install `packages/` + `executor/flows/playwright/` as editable packages inside the container OR canonicalize `PYTHONPATH`. Goal: eliminate dual-import fallback. Affected: Dockerfile, `start.sh`, all `try/except ImportError` sites. Benefit: removes the single most widespread latent bug class. Risk: Medium — requires container rebuild discipline. Order: after immediate fixes, before any monitor split.
2. **Extract `signal_policy.py` → `packages/analysis_engine/signals/`.** Goal: restore the sandbox↔detection boundary. Affected: `signal_policy.py`, `monitor_lifecycle.py`, attribution facade, tests. Benefit: unit-testable detection scoring; container-free rule tuning. Risk: Medium — the function signatures are currently Any-typed; tightening types is part of the move. Order: after container packaging lands.
3. **Split `ExtensionMonitor`** into `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant`. Goal: kill the god module. Affected: `monitor_lifecycle.py` only (if done as internal-only, the public class stays as a thin composition facade). Benefit: testable, readable, maintainable. Risk: Medium — 834 LoC split requires care; the test suite is thorough enough to catch regressions. Order: after signal_policy extraction.
4. **Add `report.activation_discovery_strategies` field + per-strategy helper extraction.** Goal: make `stop()`'s three strategies observable and individually testable. Affected: `monitor_lifecycle.py`, `contracts.py`, one new test. Benefit: failure visibility. Risk: Low. Order: during monitor split.

### Medium-term improvements (after stabilization)

1. **Subpackage the executor flat directory.** Goal: match the directory structure to the mental model. Affected: ~30 file moves. Benefit: cognitive clarity. Risk: Low if done in one PR with imports updated. Order: after monitor split.
2. **Split `packages/analysis_planner/registry.py`** into `capabilities.py`, `scenarios.py`, `event_scenario_index.py` + import-time consistency assertion. Goal: structured config + early failure. Affected: one package. Benefit: safer scenario additions. Risk: Low. Order: after monitor work.
3. **Type `raw_context`, `coverage_*`, `automation_health` on `ActivationReport`.** Goal: remove the last `dict[str, Any]` surfaces. Affected: `contracts.py`, rule helpers. Benefit: fewer runtime-only bugs. Risk: Low–Medium (will surface upstream shape drift). Order: incremental.
4. **Rename the 29 underscore-prefixed attribution facade exports** once callsites are stable. Goal: honest public API. Risk: Low. Order: after monitor split.
5. **Consolidate executor logging** into a single `logging.getLogger("extrace.executor")` channel with a dedicated handler. Goal: single log format. Risk: Low.
6. **Add `redact_secrets()` on captured content samples.** Goal: secret-leak defense-in-depth. Risk: Low.

### Avoid for now

- **Do not build a pluggable rule engine.** The current registry + pure-function rules are right-sized. A plugin loader would add complexity for no current benefit.
- **Do not split executor into microservices.** The Docker boundary is the right granularity.
- **Do not add a message bus.** `docker exec` + stdout + file-based reports is enough for a local-first tool.
- **Do not adopt OpenTelemetry.** Structured logs are enough.
- **Do not abstract `ExecutorControl` behind an interface with multiple implementations.** One sandbox, one boundary. Swap-for-tests is covered by the current dataclass.
- **Do not split `appcore/storage/crud.py` further.** The facade+ops pattern is already at the edge of useful.
- **Do not write a YAML-based rule DSL.** Rules as Python are fine for five rules. Revisit at twenty.
- **Do not move to async everywhere.** The single-worker FastAPI + sync monitor is correct for this tool.
- **Do not add a new logging framework** (structlog, loguru). `logging` suffices.

---

## 16. "Do Not Do This" List — specific to ExTrace

1. **Do not add detection logic to the executor.** `signal_policy.py` is already there and is the single biggest drift; do not make it worse. New scoring/rules go in `packages/`.
2. **Do not propagate the dual-import `try/except ImportError` pattern** to new files. Fix the packaging, then delete the fallbacks.
3. **Do not use `sys.path.insert` in runtime code.** Ever.
4. **Do not hide failures with `except Exception: pass`.** Only two files have that pattern (one is a docstring, one is a script); keep it that way.
5. **Do not introduce `shell=True`.** Ever. The codebase is currently clean.
6. **Do not concatenate strings into subprocess command lines.** List-form only.
7. **Do not bypass `ExecutorControl`.** If a workflow needs something new from the sandbox, extend `ExecutorControl`, do not call `executor.host` or `docker exec` directly.
8. **Do not bypass `appcore/storage/crud.py` / `crud_ops/`.** No raw ORM from workflows.
9. **Do not mutate `ActivationReport` in a rule.** Pure functions only.
10. **Do not add a new log channel.** Use `logging.getLogger(__name__)` or the executor `_log()` helper. Don't introduce a third.
11. **Do not add T3 (live malware) fixtures to CI.** `make test-security-live` already refuses under `CI=true`; preserve this.
12. **Do not extract `extension/` archive members without `resolve().relative_to()` containment check.**
13. **Do not treat a failed dynamic run as a clean result.** `automation_health.status = "inconclusive"` and the "no malicious without production rule" guard exist for this reason; preserve them.
14. **Do not add abstractions without two real use cases.** The `ExecutorControl` dataclass has one — and that one is the sandbox boundary, which justifies it. Most other candidates don't.
15. **Do not restart the `monitor_attribution.py` → `attribution/` split** to optimize further. Let it settle; pick up `monitor_lifecycle.py` next.
16. **Do not `xdotool type` extension-provided strings.** Literal/trusted only.
17. **Do not let the `extensions/` allow-list become a grab bag.** Keep it narrow per ADR 0004.
18. **Do not add secrets to `.env` and commit them.** Verify `.gitignore` before any new env value lands.

---

## 17. Recommended Target Architecture

**Stay a modular monolith. Tighten, don't restructure.**

```text
┌─────────────────────────────────────────────────────────────────┐
│ main.py (FastAPI app factory)                                   │
│ └── appcore/api/*   (settings, deps)                            │
└─────────────────────────────────────────────────────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ workflows/                                                      │
│   extension_catalog/       — manifest read/parse + catalog      │
│   marketplace/             — VSIX fetch + job + orchestrate     │
│   activation_reports/      — read-only report HTTP              │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
             │ (domain data)              │ (sandbox control)
             ▼                            ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│ packages/                │   │ executor/                        │
│  analysis_contracts/     │   │  control.py   — ONLY entrypoint  │
│    (Pydantic, enums,     │   │  host.py      — docker exec      │
│     schema_version,      │   │  flows/                          │
│     invariants)          │   │    playwright/                   │
│  analysis_engine/        │   │      monitor/                    │
│    rules/  (pure)        │   │      stimulus/                   │
│    signals/ ← NEW        │   │      workspace/                  │
│    runner.py             │   │      runtime_capture/            │
│    thresholds.py ← NEW   │   │      attribution/                │
│  analysis_planner/       │   │   (detection logic REMOVED)      │
│    capabilities.py ← NEW │   │  container/                      │
│    scenarios.py  ← NEW   │   │    Dockerfile, start.sh          │
│    event_index.py ← NEW  │   └──────────────────────────────────┘
└──────────────────────────┘              ▲
             ▲                            │ (raw + attributed
             │                            │  events only)
             └────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ appcore/storage/ — CRUD facade + ops + models (SQLAlchemy 2.0) │
│ appcore/db/     — engine/session                                │
│ appcore/contracts/ — API request/response schemas               │
└─────────────────────────────────────────────────────────────────┘
```

**Allowed dependencies:**

- `main.py` → `appcore.*`, `workflows.*` (routers only)
- `workflows.*` → `appcore.*`, `packages.*`, `executor.control` (ONLY this path out of executor)
- `packages.*` → nothing else in the repo (framework-agnostic)
- `executor.*` → `packages.analysis_contracts` (for type references only) — enforced via installed package, not sys.path hacks
- `appcore.*` → nothing

**Forbidden dependencies:**

- `packages.*` → `appcore | executor | workflows | ui`
- `executor.*` → `appcore | workflows`
- `workflows.*` → `executor.*` except `executor.control.*`
- Any runtime code → `sys.path.insert`
- Any code → `importlib.import_module` for sibling package access

**Data flow:**

```text
VSIX file
  ↓ [marketplace.client] extract (zip-slip + zip-bomb defended)
  ↓
Extracted extension dir
  ↓ [extension_catalog.manifest_parser]
  ↓
(typed manifest data in DB via crud_ops)
  ↓
Trigger plan (packages.analysis_planner → TriggerPayload)
  ↓ [executor.control.reset_sandbox → install_extension → run_automation]
  ↓
Raw events (runtime_capture: network, fs, exthost)
  ↓ (attribution annotates to target / near-target / noise)
  ↓
ActivationReport on disk (schema-versioned, legacy-migration-warned)
  ↓ [workflows.marketplace.analysis_reports loads]
  ↓
packages.analysis_engine.signals → (risk signals with confidence tiers)
  ↓
packages.analysis_engine.runner → rules → findings → verdict
  ↓
DetectionReport on disk
  ↓ [workflows.activation_reports serves over HTTP]
  ↓
UI
```

**Where things live:**

- Static analysis → `workflows/extension_catalog/manifest_parser.py` (stays).
- Dynamic execution → `executor/flows/playwright/` (stays; internally subpackage).
- Detection → `packages/analysis_engine/` (stays; gains `signals/` module).
- Reporting assembly → move out of `monitor_lifecycle.py` into a `ReportAssembler` class in `executor/flows/playwright/monitor/`.
- Infrastructure → `appcore/db`, `appcore/storage`, `appcore/api`, `executor/host.py`, `executor/container/` (stays).

---

## 18. Final Verdict

**1. Is the codebase currently clean enough to continue building on?**

Yes. The architecture tests, contract discipline, CRUD channeling, and sandbox boundary give this repo a stronger foundation than most security tools at this stage. You can safely add new rules, new scenarios, and new UI surfaces without blocking on a refactor.

**2. What is the biggest architectural risk?**

Detection scoring (`signal_policy.py`) living inside the executor container, reached via `sys.path` manipulation and dynamic import. It breaks the static↔dynamic↔detection separation that the rest of the codebase enforces.

**3. What is the biggest code quality risk?**

`monitor_lifecycle.py` at 834 LoC with five mixed responsibilities. The three-strategy `stop()` method is the hotspot. This file is where every future change lands by default.

**4. What is the biggest security engineering risk?**

No zip-bomb guard on VSIX extraction. Zip-slip is defended, but a malicious VSIX with an extreme compression ratio will take down the operator's host.

**5. What is the biggest overengineering risk?**

[packages/analysis_planner/registry.py](../packages/analysis_planner/registry.py) at 669 LoC — Python-as-static-config with no consistency check. It is not hurting anything today but is where the project accumulates planner debt.

**6. What should be fixed before adding more features?**

In order:

1. Verify `.env` is gitignored.
2. Add zip-bomb guards to VSIX extraction.
3. Resolve container import mode — install `packages/` + executor flows as real packages inside the container. This unblocks #4 and #5.
4. Move `signal_policy.py` into `packages/analysis_engine/signals/`.
5. Split `ExtensionMonitor`.

**7. What should not be touched yet?**

- `ExecutorControl` dataclass — it's exactly right.
- `packages/analysis_contracts/` — strongest module in the repo.
- `packages/analysis_engine/runner.py` — clean, small, correct.
- `tests/architecture/test_import_graph.py` — gold; extend it, don't modify it.
- `workflows/marketplace/client.py::_extract_vsix_to_dir` — zip-slip portion is correct; only add the size guards.
- Docker-compose + Dockerfile — stable.

**8. What is the next single best improvement?**

**Add the zip-bomb guard and verify `.env` gitignore status — today, in one small PR.** These are a one-hour combined change and close the only two security gaps with operator-host impact. After that lands, the container import-mode resolution is the next move, because it unblocks the signal-policy extraction that in turn unblocks the monitor split.

**Overall verdict:** Architecture status is **mostly healthy with localized, fixable risks**. The project is moving *toward* a clean modular monolith, not away from it. Structural intervention is not needed; targeted, small refactors are.
