# Marketplace + Workflow Tests

`Last Updated: 2026-05-05`

`tests/workflows/` — workflow router/service/parser/job_service tests.
Lane shape: [`../TESTING.md`](../TESTING.md). Layer file map:
[`../structure/test-layout.md`](../structure/test-layout.md).

## `tests/workflows/extension_catalog/`

- `test_package_parser.py` — manifest parsing surface.
- `test_router.py` — `/createExtension` and `/api/extensions/*`.
- `test_service.py` — `create_extension_by_name` +
  `create_extension_from_directory` orchestration.

## `tests/workflows/activation_reports/`

- `test_router.py` — `/api/activations`, `/api/activations/latest`,
  `/api/activations/{name}` + retry-on-OSError + latest fallback.
- `test_bundle_endpoint.py` — bundle download + W8-5 path-traversal
  guard (router-level regex; W8-5 consolidation landed `2026-04-29`).

## `tests/workflows/marketplace/`

- `test_router.py` — `/api/marketplace/search|download|analyze[/start]`
  - cancel endpoint surface. Code comment at line 2009 references
  `[FOLLOWUP simulation-progress-cancel]`.
- `test_client.py` — `download_and_extract_vsix` + retry behavior.
- `test_vsix_hardening.py` — W8-1 zip-bomb / entry-traversal guard
  (5 cases: normal, oversize, ratio, file-count, path-traversal).
- `test_identity.py` — W8-2 `safe_marketplace_slug` happy + 5
  adversarial (path traversal, absolute, null byte, unicode confusable,
  overlength).
- `test_analysis_planner.py` — trigger plan selection + layered
  fallback.
- `test_analysis_bundle.py` — analysis bundle shaping.
- `test_analysis_execution_helpers.py` — heartbeat / load tests +
  `[FOLLOWUP simulation-progress-cancel]` cancel-after-finish race
  evidence (line 238 references the verification gap closed on
  `feat/w8-2-and-reviewer-feedback-gaps`).
- `test_triggers.py` — trigger selection + failure handling.
- `test_job_service.py` — job lifecycle + `is_job_cancelled` polling.

## Architecture Tests Touching Marketplace

- `tests/architecture/test_marketplace_identity_concat.py` (W8-2) —
  blocks raw `publisher/name/version` filesystem-path concat outside
  `packages.marketplace_identity`.

## Adding A Workflow Test

- New router/service → `tests/workflows/<workflow>/`.
- New marketplace adversarial defense → mirror the W8-1/W8-2/W8-3
  pattern (subsystem-local lane).
- New trigger plan branch → `test_analysis_planner.py` +
  `test_triggers.py`.
- New cancel-related behavior → `test_router.py` + `test_job_service.py`
  - `test_analysis_execution_helpers.py`.
