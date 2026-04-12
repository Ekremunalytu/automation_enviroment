from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from appcore.contracts.schemas import (
    ExtensionCapabilitiesSchema,
    ExtensionContributesSchema,
    ExtensionSchema,
)
from workflows.extension_catalog import service


def test_create_extension_by_name_success(db_session: Session):
    """Test successful creation of extension via service."""
    mock_pkg_json = {
        "name": "test-ext",
        "publisher": "test-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.service.find_json_in_dir",
            return_value=mock_pkg_json,
        ),
        patch("workflows.extension_catalog.service.parse_npm_fields", return_value={}),
        patch(
            "workflows.extension_catalog.service.parse_extra_fields", return_value={}
        ),
        patch(
            "workflows.extension_catalog.service.parse_capabilities",
            return_value={"untrusted_supported": "supported"},
        ),
        patch(
            "workflows.extension_catalog.service.parse_scripts",
            return_value=[{"script_name": "test", "script_command": {}}],
        ),
        patch(
            "workflows.extension_catalog.service.parse_activation_events",
            return_value=[{"event_type": "*"}],
        ),
        patch(
            "workflows.extension_catalog.service.parse_contributes",
            return_value={"commands": [{"command_id": "test.cmd", "title": "Test"}]},
        ),
        patch(
            "workflows.extension_catalog.service.create_db_extension"
        ) as mock_create_db,
    ):
        mock_ext = MagicMock(id=1)
        mock_ext.name = "test-ext"
        mock_create_db.return_value = mock_ext

        result = service.create_extension_by_name(db_session, "test-ext")

        assert result.name == "test-ext"
        mock_create_db.assert_called_once()

        # Verify call args
        args = mock_create_db.call_args[0]
        assert isinstance(args[1], ExtensionSchema)
        assert isinstance(args[2], ExtensionCapabilitiesSchema)
        assert isinstance(args[3], list)  # Scripts
        assert isinstance(args[4], list)  # Activation Events
        assert isinstance(args[5], ExtensionContributesSchema)


def test_create_extension_by_name_not_found(db_session: Session):
    """Test creation when extension not found in filesystem."""
    with patch(
        "workflows.extension_catalog.service.find_json_in_dir", return_value=None
    ):
        result = service.create_extension_by_name(db_session, "ghost-ext")
        assert result is None


def test_create_extension_from_directory_success(db_session: Session):
    """Specific directory registration should bypass name-only scanning."""
    extension_dir = MagicMock()
    mock_pkg_json = {
        "name": "python",
        "publisher": "ms-python",
        "version": "2025.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.service.get_package_json",
            return_value=mock_pkg_json,
        ),
        patch(
            "workflows.extension_catalog.service._create_extension_from_package_json",
        ) as mock_create,
    ):
        mock_extension = MagicMock(id=7)
        mock_create.return_value = mock_extension

        result = service.create_extension_from_directory(
            db_session,
            extension_dir,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )

    assert result is mock_extension
    mock_create.assert_called_once_with(db_session, mock_pkg_json)


def test_create_extension_from_directory_rejects_manifest_mismatch(
    db_session: Session,
):
    """Downloaded manifest must match the requested publisher/name/version."""
    extension_dir = MagicMock()
    mock_pkg_json = {
        "name": "python",
        "publisher": "wrong-publisher",
        "version": "2025.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.service.get_package_json",
            return_value=mock_pkg_json,
        ),
        pytest.raises(service.ExtensionManifestMismatchError, match="publisher"),
    ):
        service.create_extension_from_directory(
            db_session,
            extension_dir,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_create_extension_by_name_no_extra_data(db_session: Session):
    """Test creation with minimal data (no scripts, caps, etc)."""
    mock_pkg_json = {
        "name": "minimal-ext",
        "publisher": "test-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.service.find_json_in_dir",
            return_value=mock_pkg_json,
        ),
        patch(
            "workflows.extension_catalog.service.parse_npm_fields", return_value=None
        ),
        patch(
            "workflows.extension_catalog.service.parse_extra_fields", return_value=None
        ),
        patch(
            "workflows.extension_catalog.service.parse_capabilities", return_value=None
        ),
        patch("workflows.extension_catalog.service.parse_scripts", return_value=None),
        patch(
            "workflows.extension_catalog.service.parse_activation_events",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.service.parse_contributes", return_value=None
        ),
        patch(
            "workflows.extension_catalog.service.create_db_extension"
        ) as mock_create_db,
    ):
        mock_ext = MagicMock(id=2)
        mock_ext.name = "minimal-ext"
        mock_create_db.return_value = mock_ext

        result = service.create_extension_by_name(db_session, "minimal-ext")

        assert result.name == "minimal-ext"
        mock_create_db.assert_called_once()

        # Verify None passed for optional schemas
        args = mock_create_db.call_args[0]
        assert args[2] is None  # capabilities
        assert args[3] is None  # scripts
        assert args[4] is None  # activation events
        assert args[5] is None  # contributes


def test_get_all_extensions_basic(db_session: Session):
    """Test passthrough to CRUD for basic info."""
    with patch(
        "workflows.extension_catalog.service.get_db_extensions_base_info"
    ) as mock_get:
        service.get_all_extensions_basic(db_session)
        mock_get.assert_called_once_with(db_session)


def test_get_all_extensions_all(db_session: Session):
    """Test passthrough to CRUD for all info."""
    with patch(
        "workflows.extension_catalog.service.get_extensions_all_info"
    ) as mock_get:
        service.get_all_extensions_all(db_session, skip=10, limit=20)
        mock_get.assert_called_once_with(db_session, skip=10, limit=20)


def test_search_extension_by_name(db_session: Session):
    """Test search passthrough."""
    with patch(
        "workflows.extension_catalog.service.search_db_extension"
    ) as mock_search:
        service.search_extension_by_name(db_session, "ext", "pub", "1.0")
        mock_search.assert_called_once_with(db_session, "ext", "pub", "1.0")


def test_delete_extension_by_name(db_session: Session):
    """Test delete passthrough."""
    with patch(
        "workflows.extension_catalog.service.delete_db_extension"
    ) as mock_delete:
        service.delete_extension_by_name(db_session, "ext", "pub", "1.0")
        mock_delete.assert_called_once_with(db_session, "ext", "pub", "1.0")


def test_get_extension_scripts(db_session: Session):
    """Test script retrieval passthrough."""
    with patch(
        "workflows.extension_catalog.service.get_db_extension_scripts"
    ) as mock_get:
        service.get_extension_scripts(db_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_activation_events(db_session: Session):
    """Test activation events retrieval passthrough."""
    with patch(
        "workflows.extension_catalog.service.get_db_extension_activation_events"
    ) as mock_get:
        service.get_extension_activation_events(db_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_capabilities(db_session: Session):
    """Test capability retrieval passthrough."""
    with patch(
        "workflows.extension_catalog.service.get_db_extension_capabilities"
    ) as mock_get:
        service.get_extension_capabilities(db_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_contributes_all(db_session: Session):
    """Test contributes retrieval passthrough."""
    with patch(
        "workflows.extension_catalog.service.get_db_extension_contributes"
    ) as mock_get:
        service.get_extension_contributes_all(db_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_contributes_commands(db_session: Session):
    """Test contributes commands retrieval passthrough."""
    with patch(
        "workflows.extension_catalog.service.get_db_extension_contributes_commands"
    ) as mock_get:
        service.get_extension_contributes_commands(db_session, "ext")
        mock_get.assert_called_once()
