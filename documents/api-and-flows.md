# API And Request Flows

This page keeps the concrete backend flow and route reference out of the root
README while preserving the operational details.

## Static Catalog Ingestion

Route:

```text
POST /createExtension
```

Flow:

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.manifest_reader`
4. `workflows.extension_catalog.manifest_parser`
5. `appcore.contracts.schemas`
6. `appcore.storage.crud`
7. PostgreSQL

The important invariant is that manifest data is validated with Pydantic before
database insertion.

## Marketplace Download

Route:

```text
POST /api/marketplace/download
```

Flow:

1. `workflows.marketplace.client` downloads and extracts a `.vsix`.
2. `workflows.extension_catalog.service.create_extension_from_directory`
   parses the extracted extension.
3. `appcore.storage.crud` persists validated manifest data.

Marketplace input should be treated as adversarial.

## Sandbox Analysis

Routes:

```text
POST /api/marketplace/analyze
POST /api/marketplace/analyze/start
```

Flow:

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.job_service`
4. `executor.control`
5. `executor.host` Docker exec wrapper
6. `python -m executor.flows.playwright.entrypoint`
7. Reports written under `output/`
8. Async job metadata persisted in PostgreSQL `analysis_jobs`

Notes:

- `POST /api/marketplace/analyze` is the direct request/response path.
- `POST /api/marketplace/analyze/start` is the background path used by the UI.
- Dynamic analysis defaults off. Both routes read
  `dynamic_analysis_enabled` at request time and return HTTP 409 with
  `dynamic_analysis_disabled` until the operator enables it through
  `PUT /api/settings/executor/preferences`.
- Marketplace search, download, catalog ingest, and static pre-check are not
  disabled by this preference.
- Only one background analysis should run at a time in the intended sandbox
  deployment.
- Startup fails fast if the `analysis_jobs` storage path is unavailable or the
  required migration has not been applied.
- Trigger planning may choose layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.

## Extension Catalog Routes

- `GET /`
- `GET /health`
- `GET /searchExtension`
- `GET /getExtensionsBaseInfo`
- `GET /getExtensionsAllInfo`
- `POST /createExtension`
- `DELETE /deleteExtension`
- `GET /getExtensionScripts`
- `GET /getExtensionActivationEvents`
- `GET /getExtensionCapabilities`
- `GET /getExtensionContributesAll`
- `GET /getExtensionContributesCommands`

## Activation Report Routes

- `GET /api/activations`
- `GET /api/activations/latest`
- `GET /api/activations/{name}`

## Marketplace And Analysis Routes

- `GET /api/marketplace/search`
- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`
- `POST /api/marketplace/analyze/{job_id}/cancel`

## Operator Settings Routes

- `GET /api/settings/security/thresholds`
- `PUT /api/settings/security/thresholds`
- `GET /api/settings/executor/preferences`
- `PUT /api/settings/executor/preferences`

`dynamic_analysis_enabled` is a strict boolean persisted as an integer-backed
operator setting. Its default is `false`; malformed non-boolean updates are
rejected without changing the effective value.

## Appliance Health Route

- `GET /api/system/health`

This read-only aggregate returns:

- API status, version, process uptime, and process start time;
- catalog record count, database dialect, and latest catalog write;
- bounded Docker state for the dynamic sandbox and static analyzer; and
- hostname, platform, kernel, Python version, disk usage, and observation time.

The endpoint normalizes container state instead of returning raw Docker daemon
output. Individual service failures degrade only that service entry so the
remaining measured facts stay available.

## Reading A Job

The most useful status route is:

```text
GET /api/marketplace/analyze/{job_id}
```

Use it to distinguish:

- queued or running jobs,
- failed jobs,
- cancelled jobs,
- completed jobs,
- attempted-only behavior,
- runtime health problems,
- report paths produced by the scan.

Do not infer success only from a command being attempted. The report health and
verification fields are part of the result.
