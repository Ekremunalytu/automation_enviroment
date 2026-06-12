"""W11-7: focused tests for the manifest hydration pipeline.

Pins the private `_create_extension_from_package_json` and
`_validate_manifest_identity` helpers at their real module path so a
later reshuffle that moves them away from `manifest_to_schema.py`
fails here. Public callers exercise these via `lifecycle.py`; this
file mocks the parse_* / `create_db_extension` collaborators directly.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from appcore.contracts.schemas import (
    ExtensionCapabilitiesSchema,
    ExtensionContributesSchema,
    ExtensionSchema,
)
from workflows.extension_catalog import manifest_to_schema
from workflows.extension_catalog.manifest_to_schema import (
    ExtensionManifestMismatchError,
    _create_extension_from_package_json,
    _validate_manifest_identity,
)


def test_create_extension_from_package_json_full_pipeline(mock_session: Session):
    """All parse_* helpers fire and their schemas reach `create_db_extension`."""
    mock_pkg_json = {
        "name": "test-ext",
        "publisher": "test-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_npm_fields",
            return_value={},
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_extra_fields",
            return_value={},
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_capabilities",
            return_value={"untrusted_supported": "supported"},
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_scripts",
            return_value=[{"script_name": "test", "script_command": {}}],
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_activation_events",
            return_value=[{"event_type": "*"}],
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_contributes",
            return_value={"commands": [{"command_id": "test.cmd", "title": "Test"}]},
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.create_db_extension"
        ) as mock_create_db,
    ):
        mock_ext = MagicMock(id=1)
        mock_ext.name = "test-ext"
        mock_create_db.return_value = mock_ext

        result = _create_extension_from_package_json(mock_session, mock_pkg_json)

        assert result.name == "test-ext"
        mock_create_db.assert_called_once()

        args = mock_create_db.call_args[0]
        assert isinstance(args[1], ExtensionSchema)
        assert isinstance(args[2], ExtensionCapabilitiesSchema)
        assert isinstance(args[3], list)
        assert isinstance(args[4], list)
        assert isinstance(args[5], ExtensionContributesSchema)


def test_create_extension_from_package_json_no_extra_data(mock_session: Session):
    """When parse_* helpers return None, optional schemas reach CRUD as None."""
    mock_pkg_json = {
        "name": "minimal-ext",
        "publisher": "test-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_npm_fields",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_extra_fields",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_capabilities",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_scripts",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_activation_events",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_contributes",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.create_db_extension"
        ) as mock_create_db,
    ):
        mock_ext = MagicMock(id=2)
        mock_ext.name = "minimal-ext"
        mock_create_db.return_value = mock_ext

        result = _create_extension_from_package_json(mock_session, mock_pkg_json)

        assert result.name == "minimal-ext"
        mock_create_db.assert_called_once()

        args = mock_create_db.call_args[0]
        assert args[2] is None  # capabilities
        assert args[3] is None  # scripts
        assert args[4] is None  # activation events
        assert args[5] is None  # contributes


def test_create_extension_with_list_form_configuration(mock_session: Session):
    """`contributes.configuration` as a list flows through hydration intact.

    Regression for the GitHub Copilot Chat ingest failure: VS Code permits
    `contributes.configuration` to be either a single object or an array of
    config sections. Copilot ships the array form, which previously raised a
    pydantic `dict_type` error while building `ExtensionContributesSchema`,
    aborting the whole catalog write. The hydration path must accept the list
    and pass it through to `create_db_extension` unchanged.
    """
    mock_pkg_json = {
        "name": "copilot-chat",
        "publisher": "GitHub",
        "version": "0.48.1",
        "engines": {"vscode": "^1.120.0"},
    }
    list_form_configuration = [
        {"title": "GitHub Copilot", "properties": {"copilot.enable": {}}},
        {"title": "Advanced", "properties": {"copilot.advanced": {}}},
    ]

    with (
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_npm_fields",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_extra_fields",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_capabilities",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_scripts",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_activation_events",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.parse_contributes",
            return_value={"configuration": list_form_configuration},
        ),
        patch(
            "workflows.extension_catalog.manifest_to_schema.create_db_extension"
        ) as mock_create_db,
    ):
        mock_ext = MagicMock(id=3)
        mock_ext.name = "copilot-chat"
        mock_create_db.return_value = mock_ext

        result = _create_extension_from_package_json(mock_session, mock_pkg_json)

        assert result.name == "copilot-chat"
        mock_create_db.assert_called_once()

        contributes_schema = mock_create_db.call_args[0][5]
        assert isinstance(contributes_schema, ExtensionContributesSchema)
        assert isinstance(contributes_schema.configuration, list)
        assert len(contributes_schema.configuration) == 2
        assert contributes_schema.configuration[0]["title"] == "GitHub Copilot"


def test_validate_manifest_identity_accepts_match():
    """All three expected fields match → no exception."""
    pkg = {"name": "python", "publisher": "ms-python", "version": "2025.0.0"}

    _validate_manifest_identity(
        pkg,
        expected_name="python",
        expected_publisher="ms-python",
        expected_version="2025.0.0",
    )


def test_validate_manifest_identity_rejects_publisher_mismatch():
    """Publisher mismatch surfaces with the offending value in the message."""
    pkg = {"name": "python", "publisher": "wrong-publisher", "version": "2025.0.0"}

    with pytest.raises(ExtensionManifestMismatchError, match="publisher"):
        _validate_manifest_identity(
            pkg,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_validate_manifest_identity_rejects_name_mismatch():
    """Name mismatch surfaces with the offending value."""
    pkg = {"name": "different", "publisher": "ms-python", "version": "2025.0.0"}

    with pytest.raises(ExtensionManifestMismatchError, match="name"):
        _validate_manifest_identity(
            pkg,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_validate_manifest_identity_rejects_version_mismatch():
    """Version mismatch surfaces with the offending value."""
    pkg = {"name": "python", "publisher": "ms-python", "version": "9.9.9"}

    with pytest.raises(ExtensionManifestMismatchError, match="version"):
        _validate_manifest_identity(
            pkg,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_validate_manifest_identity_lists_multiple_mismatches():
    """Two-field mismatch lists both fields in the same error message."""
    pkg = {"name": "different", "publisher": "wrong-publisher", "version": "2025.0.0"}

    with pytest.raises(ExtensionManifestMismatchError) as exc_info:
        _validate_manifest_identity(
            pkg,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )

    message = str(exc_info.value)
    assert "name" in message
    assert "publisher" in message


def test_validate_manifest_identity_skips_unspecified_fields():
    """Caller passing None for an expected_* field skips that field's check."""
    pkg = {"name": "python", "publisher": "anyone", "version": "9.9.9"}

    _validate_manifest_identity(
        pkg,
        expected_name="python",
        expected_publisher=None,
        expected_version=None,
    )


def test_extension_manifest_mismatch_error_is_value_error_subclass():
    """Existing callers catching ValueError must continue to catch the mismatch."""
    assert issubclass(ExtensionManifestMismatchError, ValueError)


def test_module_path_pins_manifest_to_schema():
    """W11-7 module-path pin: hydration helpers stay in manifest_to_schema."""
    assert _create_extension_from_package_json.__module__ == (
        "workflows.extension_catalog.manifest_to_schema"
    )
    assert _validate_manifest_identity.__module__ == (
        "workflows.extension_catalog.manifest_to_schema"
    )
    assert ExtensionManifestMismatchError.__module__ == (
        "workflows.extension_catalog.manifest_to_schema"
    )
    assert manifest_to_schema.__name__ == (
        "workflows.extension_catalog.manifest_to_schema"
    )
