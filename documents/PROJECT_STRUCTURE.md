# Project Structure

`Last Updated: 2026-04-25`

This is the current top-level layout and placement guidance for the refactored
repository.

## Top-Level Layout

```text
alembic/                   Schema migrations
appcore/                   Shared platform code
docker/                    API container build files
docs/                      Narrow risk notes outside the main doc set
documents/                 Canonical project documentation
executor/                  Sandbox host wrapper + container runtime
extensions/                Downloaded/extracted VSIX fixtures and samples
packages/                  Framework-agnostic contracts and analysis logic
output/                    Generated reports and runtime artifacts
scripts/                   Small maintenance helpers
tests/                     Python test suite
ui/                        Primary React analyst console
workflows/                 Canonical business workflows
```

## Placement Rules

- Put reusable platform code in `appcore/`.
- Put framework-agnostic contracts or planning logic in `packages/`.
- Put workflow-specific routers, services, parsers, and trigger logic in the
  matching `workflows/<name>/` package.
- Put sandbox runtime code in `executor/`.
- Put analyst-facing frontend code in `ui/`.
- Keep generated artifacts in `output/`; do not treat them as source code.
- Keep extension fixtures and downloaded VSIX artifacts in `extensions/`.
- If a change affects persisted catalog schema, pair it with Alembic updates in
  `alembic/versions/`.

## Canonical Paths

- `main.py`
- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `packages/analysis_contracts/`
- `packages/analysis_planner/`
- `workflows/extension_catalog/`
- `workflows/activation_reports/`
- `workflows/marketplace/`
- `executor/control.py`
- `executor/host.py`

## Workflow Layout

```text
workflows/
  activation_reports/
    router.py
  extension_catalog/
    manifest_parser.py
    manifest_reader.py
    package_parser.py
    router.py
    service.py
  marketplace/
    analysis_errors.py
    analysis_execution.py
    analysis_reports.py
    analysis_service.py
    client.py
    job_service.py
    router.py
    trigger_service.py
    triggers.py
```

## UI Layout

```text
ui/
  src/
    app/
      App.tsx
      layout/
    components/
      evidence/
      marketplace/
      simulation/
      ui/
    features/
      marketplace/
      reports/
      simulation/
    lib/
      adapters/
      api/
      charts/
      rules/
      types/
    main.tsx
    index.css
  smoke/
  Dockerfile
  README.md
```

Notes:

- The routed analyst surfaces are `/marketplace`, `/simulation`, and `/reports`.
- Evidence, inspector, and rule-draft behavior is largely composed from
  `ui/src/components/evidence/` plus adapters and draft helpers in
  `ui/src/lib/`.
- Backend-owned UI contract types are generated into `ui/src/lib/types/`.

## Executor Layout

```text
executor/
  control.py
  host.py
  container/
    Dockerfile
    launch_vscode.sh
    requirements.txt
    start.sh
  flows/
    harness_extension/
      extension.js
      package.json
    playwright/
      annotation.py
      attribution/
        __init__.py
        events.py
        links.py
      automation.py
      capture.py
      commands.py
      debug.py
      editor.py
      entrypoint.py
      entrypoint_cli.py
      entrypoint_runner.py
      entrypoint_triggers.py
      health.py
      health_reconciliation.py
      health_runtime_facts.py
      health_summary.py
      keyboard.py
      language_samples.py
      monitor.py
      monitor_lifecycle.py
      monitor_payload.py
      monitor_records.py
      monitor_runtime.py
      monitor_sources.py
      monitor_support.py
      monitor_types.py
      panel.py
      reload_vscode.py
      report_builder.py
      runtime_capture/
        _shared.py
        events.py
        extension_host.py
        filesystem.py
        log_summary.py
        network.py
      scenarios/
        common.py
        editing.py
        registry.py
        runtime.py
        workbench.py
      reset_state.py
      settings.py
      sidebar.py
      signal_facts.py
      signal_policy.py
      signals.py
      stimulus.py
      stimulus_attempts.py
      stimulus_materializers.py
      stimulus_passes.py
      stimulus_prerequisites.py
      stimulus_types.py
      terminal.py
      triggers.py
      vscode.py
      wait_helpers.py
      workspace.py
      workspace_seed_data.py
      workspace_seed_home.py
      workspace_seed_project_1.py
      workspace_seed_project_2.py
      workspace_seed_project_3.py
```

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  architecture/
    test_import_graph.py
  executor/
    conftest.py
    test_container_dockerfile.py
    test_playwright_automation.py
    test_playwright_commands.py
    test_playwright_crash_classifier.py
    test_playwright_entrypoint.py
    test_playwright_health_summary.py
    test_playwright_helpers.py
    test_playwright_monitor_attribution.py
    test_playwright_monitor_lifecycle.py
    test_playwright_monitor_package_import.py
    test_playwright_monitor_runtime.py
    test_playwright_reload.py
    test_playwright_stimulus.py
    test_reset_state.py
    test_signal_policy.py
    test_workspace.py
  platform/
    api/
      test_app_runtime.py
      test_config.py
      test_deps.py
      test_fixtures.py
    contracts/
      fixtures/
      test_analysis_fixture_baselines.py
      test_detection_report.py
      test_report_builder_contract.py
      test_schemas.py
      test_verdict_rollup.py
    engine/
      test_rule_runner.py
    storage/
      test_analysis_jobs.py
      test_crud.py
    test_canonical_imports.py
  security/
    helpers.py
    rules/
      test_a1_credential_read_then_network.py
      test_a2_startup_network_beacon.py
      test_a3_typosquat.py
      test_a4_workspace_exfil.py
      test_a6_startup_ui_prompt.py
      test_rule_attribution.py
    test_benign_silence.py
    test_canary_end_to_end.py
    test_detection_report_invariants.py
    test_fixture_hygiene.py
    test_rule_coverage.py
    test_rule_validation.py
  scanner/
    test_executor.py
  smoke/
    test_marketplace_analysis_smoke.py
  workflows/
    activation_reports/
      test_bundle_endpoint.py
      test_router.py
    extension_catalog/
      test_package_parser.py
      test_router.py
      test_service.py
    marketplace/
      fixtures/
      test_analysis_bundle.py
      test_analysis_execution_helpers.py
      test_analysis_planner.py
      test_client.py
      test_router.py
      test_triggers.py
```

UI tests live under `ui/src/**/*.test.ts(x)`.

## Generated and Reference Areas

- `extensions/`
  - downloaded VSIX artifacts, extracted extension directories, and pinned test
    fixtures
  - `extensions/malicious/` contains malicious-fixture manifests and canary
    scaffold metadata
- `output/`
  - activation reports and executor-side runtime artifacts
- `documents/`
  - architecture, executor, testing, roadmap, and semantics notes
- `docs/`
  - narrower risk notes such as `docs/risks.md`

## Quick Change Map

- Shared config or dependency injection: `appcore/api/`
- Shared schema or model change: `appcore/contracts/`, `appcore/storage/`,
  `alembic/versions/`, matching tests
- Framework-agnostic contracts or planner logic: `packages/analysis_contracts/`
  or `packages/analysis_planner/`
- Catalog feature: `workflows/extension_catalog/`
- Activation report behavior: `workflows/activation_reports/`
- Marketplace download/analysis feature: `workflows/marketplace/`
- Sandbox runtime behavior: `executor/control.py`, `executor/host.py`, or
  `executor/flows/playwright/`
- UI route or workspace behavior: `ui/src/features/`
- UI shared primitive: `ui/src/components/`
- UI API/adapters/rule logic: `ui/src/lib/`
- Security scaffold or malicious fixture policy:
  `packages/analysis_contracts/detection/`, `extensions/malicious/`,
  `tests/security/`, and the ADRs under `documents/adrs/`
