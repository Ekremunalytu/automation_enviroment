from __future__ import annotations

import appcore.api.config as app_config
import appcore.api.deps as app_deps
import appcore.contracts.schemas as app_schemas
import appcore.db.session as app_session
import appcore.storage.crud as app_crud
import appcore.storage.crud_ops.analysis_jobs as analysis_jobs_facade
import appcore.storage.crud_ops.analysis_jobs.lifecycle as analysis_jobs_lifecycle
import appcore.storage.crud_ops.analysis_jobs.steps as analysis_jobs_steps
import appcore.storage.models as app_models
import executor.host as executor_host
import packages.analysis_contracts as analysis_contracts
import packages.analysis_planner as analysis_planner
import workflows.extension_catalog.lifecycle as extension_lifecycle
import workflows.extension_catalog.manifest_to_schema as extension_manifest_to_schema
import workflows.extension_catalog.package_parser as package_parser
import workflows.extension_catalog.service as extension_service
import workflows.marketplace.client as marketplace_client
import workflows.marketplace.triggers as marketplace_triggers


def test_canonical_modules_export_expected_symbols() -> None:
    assert app_config.settings is not None
    assert callable(app_deps.get_db)
    assert callable(app_crud.create_extension)
    assert app_session.SessionLocal is not None
    assert app_models.Extension is not None
    assert package_parser.search_extension is not None
    assert extension_service.create_extension_by_name is not None
    assert extension_lifecycle.create_extension_by_name is not None
    assert extension_lifecycle.search_extension_by_name is not None
    assert extension_manifest_to_schema.ExtensionManifestMismatchError is not None
    assert callable(extension_manifest_to_schema._validate_manifest_identity)
    assert marketplace_client.get_vsix_path is not None
    assert marketplace_triggers.select_scenarios is not None
    assert app_schemas.ExtensionSchema is not None
    assert analysis_contracts.ActivationReport is not None
    assert analysis_contracts.TriggerPayload is not None
    assert callable(analysis_planner.select_scenarios)
    assert executor_host.ExecutorError is not None
    assert callable(analysis_jobs_facade.cancel_analysis_job)
    assert callable(analysis_jobs_lifecycle.cancel_analysis_job)
    assert callable(analysis_jobs_steps.update_analysis_job_step)
    assert (
        analysis_jobs_facade.JobNotCancellableError
        is analysis_jobs_lifecycle.JobNotCancellableError
    )
    assert (
        analysis_jobs_facade.update_analysis_job_step
        is analysis_jobs_steps.update_analysis_job_step
    )
