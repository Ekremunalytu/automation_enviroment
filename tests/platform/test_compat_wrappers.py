from __future__ import annotations

import appcore.api.config as app_config
import appcore.api.deps as app_deps
import appcore.contracts.schemas as app_schemas
import appcore.db.session as app_session
import appcore.storage.crud as app_crud
import appcore.storage.models as app_models
import core.config as legacy_config
import core.deps as legacy_deps
import crud.crud as legacy_crud
import database.session as legacy_session
import models.models as legacy_models
import scanner.json_parser as legacy_json_parser
import scanner.marketplace as legacy_marketplace
import scanner.service as legacy_service
import scanner.triggers as legacy_triggers
import schemas.schemas as legacy_schemas
import workflows.extension_catalog.package_parser as workflow_parser
import workflows.extension_catalog.service as workflow_service
import workflows.marketplace.client as workflow_marketplace
import workflows.marketplace.triggers as workflow_triggers


def test_legacy_wrappers_still_export_new_modules() -> None:
    assert legacy_config.settings is app_config.settings
    assert legacy_deps.get_db is app_deps.get_db
    assert legacy_crud.create_extension is app_crud.create_extension
    assert legacy_session.SessionLocal is app_session.SessionLocal
    assert legacy_models.Extension is app_models.Extension
    assert legacy_json_parser.search_extension is workflow_parser.search_extension
    assert legacy_marketplace.get_vsix_path is workflow_marketplace.get_vsix_path
    assert (
        legacy_service.create_extension_by_name
        is workflow_service.create_extension_by_name
    )
    assert legacy_triggers.select_scenarios is workflow_triggers.select_scenarios
    assert legacy_schemas.ExtensionSchema is app_schemas.ExtensionSchema
