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
