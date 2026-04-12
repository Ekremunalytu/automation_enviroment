from __future__ import annotations

import appcore.api.config as app_config
import appcore.api.deps as app_deps
import appcore.contracts.schemas as app_schemas
import appcore.db.session as app_session
import appcore.storage.crud as app_crud
import appcore.storage.models as app_models
import executor.host as executor_host
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
    assert marketplace_client.get_vsix_path is not None
    assert marketplace_triggers.select_scenarios is not None
    assert app_schemas.ExtensionSchema is not None
    assert executor_host.ExecutorError is not None
