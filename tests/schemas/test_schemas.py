import pytest
from pydantic import ValidationError

from schemas.schemas import ExtensionSchema


def test_extension_schema_valid():
    data = {
        "name": "valid-ext",
        "publisher": "valid-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.name == "valid-ext"


def test_extension_schema_missing_field():
    data = {
        "name": "invalid-ext",
        # Missing publisher, version, engines
    }
    with pytest.raises(ValidationError) as exc:
        ExtensionSchema(**data)

    errors = exc.value.errors()
    missing_fields = [e["loc"][0] for e in errors]
    assert "publisher" in missing_fields
    assert "version" in missing_fields


def test_extension_schema_with_dependencies():
    """Test ExtensionSchema with dependencies and devDependencies fields."""
    data = {
        "name": "deps-ext",
        "publisher": "deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "dependencies": {"axios": "^1.0.0", "lodash": "^4.17.0"},
        "devDependencies": {"typescript": "^5.0.0", "@types/node": "^20.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.dependencies == {"axios": "^1.0.0", "lodash": "^4.17.0"}
    assert schema.devDependencies == {"typescript": "^5.0.0", "@types/node": "^20.0.0"}


def test_extension_schema_with_null_dependencies():
    """Test ExtensionSchema with null/missing dependencies fields."""
    data = {
        "name": "no-deps-ext",
        "publisher": "no-deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.dependencies is None
    assert schema.devDependencies is None
