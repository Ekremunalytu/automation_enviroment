import pytest
from sqlalchemy.orm import Session

from crud.crud import (
    create_extension,
    delete_extension,
    search_extension_by_name,
)
from schemas.schemas import ExtensionSchema


def test_create_extension(db_session: Session):
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
