import pytest
from sqlalchemy.orm import Session

from crud.crud import (
    create_extension,
    delete_extension,
    search_extension_by_name,
)
from schemas.schemas import ExtensionSchema


def test_create_extension(db_session: Session):
    """Test successful creation of a new extension."""
    schema = ExtensionSchema(
        name="test-ext",
        publisher="test-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Test Description",
    )
    ext = create_extension(db_session, schema)
    assert ext.id is not None
    assert ext.name == "test-ext"


def test_create_duplicate_extension(db_session: Session):
    """Test that creating a duplicate extension raises ValueError."""
    schema = ExtensionSchema(
        name="test-ext",
        publisher="test-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    create_extension(db_session, schema)

    with pytest.raises(ValueError, match="Extension already exists"):
        create_extension(db_session, schema)


def test_search_extension_by_name(db_session: Session):
    """Test searching for an extension by its name."""
    # Setup
    schema = ExtensionSchema(
        name="search-me",
        publisher="search-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    create_extension(db_session, schema)

    # Test
    result = search_extension_by_name(db_session, "search-me")
    assert result is not None
    assert result.publisher == "search-pub"

    # Test Not Found
    assert search_extension_by_name(db_session, "non-existent") is None


def test_delete_extension(db_session: Session):
    """Test deleting an extension and verifying it's gone."""
    # Setup
    schema = ExtensionSchema(
        name="delete-me",
        publisher="del-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    create_extension(db_session, schema)

    # Test
    assert delete_extension(db_session, "delete-me") is True
    assert search_extension_by_name(db_session, "delete-me") is None
    assert delete_extension(db_session, "delete-me") is False


def test_create_extension_with_new_fields(db_session: Session):
    """
    Test creating extension with new list fields.

    Verifies extensionPack, extensionDependencies, and extensionKind.
    """
    schema = ExtensionSchema(
        name="full-ext",
        publisher="full-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Extension with all new fields",
        extensionPack=["ms-python.python", "ms-python.vscode-pylance"],
        extensionDependencies=["ms-vscode.cpptools"],
        extensionKind=["workspace"],
    )
    ext = create_extension(db_session, schema)

    assert ext.id is not None
    assert ext.name == "full-ext"
    assert ext.extensionPack == ["ms-python.python", "ms-python.vscode-pylance"]
    assert ext.extensionDependencies == ["ms-vscode.cpptools"]
    assert ext.extensionKind == ["workspace"]


def test_search_extension_with_new_fields(db_session: Session):
    """Test searching extension returns new fields correctly."""
    schema = ExtensionSchema(
        name="search-new-fields",
        publisher="search-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        extensionPack=["bundle.ext1"],
        extensionDependencies=["required.ext"],
        extensionKind=["ui", "workspace"],
    )
    create_extension(db_session, schema)

    result = search_extension_by_name(db_session, "search-new-fields")

    assert result is not None
    assert result.extensionPack == ["bundle.ext1"]
    assert result.extensionDependencies == ["required.ext"]
    assert result.extensionKind == ["ui", "workspace"]
