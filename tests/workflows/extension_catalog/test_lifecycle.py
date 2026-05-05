"""W11-7: focused tests for the public extension-catalog lifecycle surface.

Pins `lifecycle.py` at its real module path so a later reshuffle that
moves these public functions away fails here. CRUD-side collaborators
and the manifest hydration helper are mocked at the `lifecycle` module
boundary; the hydration helper itself is exercised in
`test_manifest_to_schema.py`.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from workflows.extension_catalog import lifecycle
from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.extension_catalog.manifest_to_schema import (
    ExtensionManifestMismatchError,
)


def test_create_extension_by_name_success(mock_session: Session):
    """find_json_in_dir hits → hydration helper builds and returns the Extension."""
    mock_pkg_json = {
        "name": "test-ext",
        "publisher": "test-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    mock_ext = MagicMock(id=1)
    mock_ext.name = "test-ext"

    with (
        patch(
            "workflows.extension_catalog.lifecycle.find_json_in_dir",
            return_value=mock_pkg_json,
        ),
        patch(
            "workflows.extension_catalog.lifecycle._create_extension_from_package_json",
            return_value=mock_ext,
        ) as mock_create,
    ):
        result = lifecycle.create_extension_by_name(mock_session, "test-ext")

    assert result is mock_ext
    mock_create.assert_called_once_with(mock_session, mock_pkg_json)


def test_create_extension_by_name_not_found(mock_session: Session):
    """find_json_in_dir returns None → result is None and hydrator never runs."""
    with (
        patch(
            "workflows.extension_catalog.lifecycle.find_json_in_dir",
            return_value=None,
        ),
        patch(
            "workflows.extension_catalog.lifecycle._create_extension_from_package_json",
        ) as mock_create,
    ):
        result = lifecycle.create_extension_by_name(mock_session, "ghost-ext")

    assert result is None
    mock_create.assert_not_called()


def test_create_extension_from_directory_success(mock_session: Session):
    """Directory entry: get_package_json → identity check → hydrator."""
    extension_dir = MagicMock()
    mock_pkg_json = {
        "name": "python",
        "publisher": "ms-python",
        "version": "2025.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.lifecycle.get_package_json",
            return_value=mock_pkg_json,
        ),
        patch(
            "workflows.extension_catalog.lifecycle._create_extension_from_package_json",
        ) as mock_create,
    ):
        mock_extension = MagicMock(id=7)
        mock_create.return_value = mock_extension

        result = lifecycle.create_extension_from_directory(
            mock_session,
            extension_dir,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )

    assert result is mock_extension
    mock_create.assert_called_once_with(mock_session, mock_pkg_json)


def test_create_extension_from_directory_rejects_manifest_mismatch(
    mock_session: Session,
):
    """Mismatch between requested identity and on-disk manifest is rejected."""
    extension_dir = MagicMock()
    mock_pkg_json = {
        "name": "python",
        "publisher": "wrong-publisher",
        "version": "2025.0.0",
        "engines": {"vscode": "^1.0.0"},
    }

    with (
        patch(
            "workflows.extension_catalog.lifecycle.get_package_json",
            return_value=mock_pkg_json,
        ),
        pytest.raises(ExtensionManifestMismatchError, match="publisher"),
    ):
        lifecycle.create_extension_from_directory(
            mock_session,
            extension_dir,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_create_extension_from_directory_propagates_manifest_read_errors(
    mock_session: Session,
):
    """Manifest read failures propagate to the caller untouched."""
    extension_dir = MagicMock()

    with (
        patch(
            "workflows.extension_catalog.lifecycle.get_package_json",
            side_effect=PackageJsonReadError.missing(
                Path("extensions/test-ext/package.json")
            ),
        ),
        pytest.raises(PackageJsonReadError, match="missing"),
    ):
        lifecycle.create_extension_from_directory(
            mock_session,
            extension_dir,
            expected_name="python",
            expected_publisher="ms-python",
            expected_version="2025.0.0",
        )


def test_get_all_extensions_basic(mock_session: Session):
    """Pass-through to CRUD getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extensions_base_info"
    ) as mock_get:
        lifecycle.get_all_extensions_basic(mock_session)
        mock_get.assert_called_once_with(mock_session)


def test_get_all_extensions_all(mock_session: Session):
    """Pass-through to CRUD getter with pagination args forwarded."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_extensions_all_info"
    ) as mock_get:
        lifecycle.get_all_extensions_all(mock_session, skip=10, limit=20)
        mock_get.assert_called_once_with(mock_session, skip=10, limit=20)


def test_search_extension_by_name(mock_session: Session):
    """Pass-through to CRUD search; positional args forwarded in declared order."""
    with patch(
        "workflows.extension_catalog.lifecycle.search_db_extension"
    ) as mock_search:
        lifecycle.search_extension_by_name(mock_session, "ext", "pub", "1.0")
        mock_search.assert_called_once_with(mock_session, "ext", "pub", "1.0")


def test_delete_extension_by_name(mock_session: Session):
    """Pass-through to CRUD delete; positional args forwarded in declared order."""
    with patch(
        "workflows.extension_catalog.lifecycle.delete_db_extension"
    ) as mock_delete:
        lifecycle.delete_extension_by_name(mock_session, "ext", "pub", "1.0")
        mock_delete.assert_called_once_with(mock_session, "ext", "pub", "1.0")


def test_get_extension_scripts(mock_session: Session):
    """Pass-through to CRUD scripts getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extension_scripts"
    ) as mock_get:
        lifecycle.get_extension_scripts(mock_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_activation_events(mock_session: Session):
    """Pass-through to CRUD activation-events getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extension_activation_events"
    ) as mock_get:
        lifecycle.get_extension_activation_events(mock_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_capabilities(mock_session: Session):
    """Pass-through to CRUD capabilities getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extension_capabilities"
    ) as mock_get:
        lifecycle.get_extension_capabilities(mock_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_contributes_all(mock_session: Session):
    """Pass-through to CRUD contributes (all) getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extension_contributes"
    ) as mock_get:
        lifecycle.get_extension_contributes_all(mock_session, "ext")
        mock_get.assert_called_once()


def test_get_extension_contributes_commands(mock_session: Session):
    """Pass-through to CRUD contributes-commands getter."""
    with patch(
        "workflows.extension_catalog.lifecycle.get_db_extension_contributes_commands"
    ) as mock_get:
        lifecycle.get_extension_contributes_commands(mock_session, "ext")
        mock_get.assert_called_once()


def test_module_path_pins_lifecycle():
    """W11-7 module-path pin: public surface stays attached to lifecycle.py."""
    assert lifecycle.create_extension_by_name.__module__ == (
        "workflows.extension_catalog.lifecycle"
    )
    assert lifecycle.create_extension_from_directory.__module__ == (
        "workflows.extension_catalog.lifecycle"
    )
    assert lifecycle.search_extension_by_name.__module__ == (
        "workflows.extension_catalog.lifecycle"
    )
    assert lifecycle.delete_extension_by_name.__module__ == (
        "workflows.extension_catalog.lifecycle"
    )
    assert lifecycle.__name__ == "workflows.extension_catalog.lifecycle"


def test_facade_back_compat_reexports_match_lifecycle():
    """The thin `service.py` facade re-exports the same callables as `lifecycle`.

    Pin protects three external consumers of `workflows.extension_catalog.service`:
    `workflows/marketplace/router.py`, `tests/platform/test_canonical_imports.py`,
    and any caller still on the legacy import path.
    """
    from workflows.extension_catalog import manifest_to_schema, service

    assert service.create_extension_by_name is lifecycle.create_extension_by_name
    assert (
        service.create_extension_from_directory
        is lifecycle.create_extension_from_directory
    )
    assert service.search_extension_by_name is lifecycle.search_extension_by_name
    assert service.delete_extension_by_name is lifecycle.delete_extension_by_name
    assert service.get_all_extensions_basic is lifecycle.get_all_extensions_basic
    assert service.get_all_extensions_all is lifecycle.get_all_extensions_all
    assert service.get_extension_scripts is lifecycle.get_extension_scripts
    assert (
        service.get_extension_activation_events
        is lifecycle.get_extension_activation_events
    )
    assert service.get_extension_capabilities is lifecycle.get_extension_capabilities
    assert (
        service.get_extension_contributes_all is lifecycle.get_extension_contributes_all
    )
    assert (
        service.get_extension_contributes_commands
        is lifecycle.get_extension_contributes_commands
    )
    assert (
        service.ExtensionManifestMismatchError
        is manifest_to_schema.ExtensionManifestMismatchError
    )
