import pytest
from pydantic import ValidationError

from schemas.schemas import (
    ExtensionContributesSchema,
    ExtensionSchema,
)


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


def test_extension_schema_with_extension_pack():
    """Test ExtensionSchema with extensionPack field."""
    data = {
        "name": "pack-ext",
        "publisher": "pack-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionPack": ["ms-python.python", "ms-python.vscode-pylance"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack == ["ms-python.python", "ms-python.vscode-pylance"]


def test_extension_schema_with_extension_dependencies():
    """Test ExtensionSchema with extensionDependencies field."""
    data = {
        "name": "deps-ext",
        "publisher": "deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionDependencies": ["ms-vscode.cpptools", "vscjava.vscode-java-pack"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionDependencies == [
        "ms-vscode.cpptools",
        "vscjava.vscode-java-pack",
    ]


def test_extension_schema_with_extension_kind():
    """Test ExtensionSchema with extensionKind field."""
    data = {
        "name": "kind-ext",
        "publisher": "kind-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionKind": ["ui", "workspace"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionKind == ["ui", "workspace"]


def test_extension_schema_with_all_extension_fields():
    """Test ExtensionSchema with all new extension fields populated."""
    data = {
        "name": "full-ext",
        "publisher": "full-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionPack": ["bundle.ext1", "bundle.ext2"],
        "extensionDependencies": ["required.ext"],
        "extensionKind": ["workspace"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack == ["bundle.ext1", "bundle.ext2"]
    assert schema.extensionDependencies == ["required.ext"]
    assert schema.extensionKind == ["workspace"]


def test_extension_schema_with_null_extension_fields():
    """Test ExtensionSchema with null/missing extension fields."""
    data = {
        "name": "null-ext",
        "publisher": "null-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack is None
    assert schema.extensionDependencies is None
    assert schema.extensionKind is None


def test_extension_contributes_schema_defaults():
    """Test ExtensionContributesSchema default values."""
    schema = ExtensionContributesSchema()
    assert schema.configuration is None
    assert schema.keybindings == []
    assert schema.menus == []
    assert schema.authentication == []
    assert schema.terminal == []
    assert schema.commands == []


def test_extension_contributes_schema_with_children():
    """Test ExtensionContributesSchema with child contribution data."""
    data = {
        "configuration": {"title": "Config"},
        "keybindings": [
            {"key": "ctrl+k", "command": "ext.hello", "when": "editorTextFocus"}
        ],
        "commands": [{"command_id": "ext.hello", "title": "Hello"}],
        "menus": [{"menu_location": "editor/context", "command": "ext.hello"}],
        "authentication": [{"auth_id": "github", "label": "GitHub"}],
        "terminal": [{"profile_id": "ext.term", "title": "Ext Terminal"}],
    }
    schema = ExtensionContributesSchema(**data)

    assert schema.configuration == {"title": "Config"}
    assert schema.keybindings[0].command == "ext.hello"
    assert schema.commands[0].command_id == "ext.hello"
    assert schema.menus[0].menu_location == "editor/context"
    assert schema.authentication[0].auth_id == "github"
    assert schema.terminal[0].profile_id == "ext.term"
