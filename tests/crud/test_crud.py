import pytest
from sqlalchemy.orm import Session

from crud.crud import (
    create_extension,
    delete_extension,
    search_extension_by_name,
)
from schemas.schemas import (
    ExtensionContributesAuthenticationSchema,
    ExtensionContributesCommandsSchema,
    ExtensionContributesKeybindingsSchema,
    ExtensionContributesMenusSchema,
    ExtensionContributesSchema,
    ExtensionContributesTerminalSchema,
    ExtensionSchema,
)


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


def test_create_extension_with_activation_events(db_session: Session):
    """
    Test creating extension with activation events.

    Verifies that activation events are correctly parsed, stored,
    and retrieved with the extension.
    """
    from schemas.schemas import ExtensionActivationEventsSchema

    schema = ExtensionSchema(
        name="event-ext",
        publisher="event-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Extension with activation events",
    )
    events = [
        ExtensionActivationEventsSchema(event_type="onLanguage", event_value="python"),
        ExtensionActivationEventsSchema(
            event_type="onCommand", event_value="extension.activate"
        ),
        ExtensionActivationEventsSchema(event_type="*", event_value=None),
    ]

    ext = create_extension(db_session, schema, activation_events=events)

    assert ext.id is not None
    assert ext.name == "event-ext"
    assert len(ext.activation_events) == 3


def test_search_extension_with_activation_events(db_session: Session):
    """
    Test searching extension returns activation events correctly.

    Ensures that the joinedload properly fetches related activation events.
    """
    from schemas.schemas import ExtensionActivationEventsSchema

    schema = ExtensionSchema(
        name="search-events",
        publisher="search-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    events = [
        ExtensionActivationEventsSchema(
            event_type="onLanguage", event_value="typescript"
        ),
        ExtensionActivationEventsSchema(
            event_type="workspaceContains", event_value="**/.gitignore"
        ),
    ]
    create_extension(db_session, schema, activation_events=events)

    result = search_extension_by_name(db_session, "search-events")

    assert result is not None
    assert len(result.activation_events) == 2
    event_types = [e.event_type for e in result.activation_events]
    assert "onLanguage" in event_types
    assert "workspaceContains" in event_types


def test_create_extension_with_scripts(db_session: Session):
    """
    Test creating extension with scripts.

    Verifies that scripts are correctly parsed, stored,
    and retrieved with the extension.
    """
    from schemas.schemas import ExtensionScriptsSchema

    schema = ExtensionSchema(
        name="scripts-ext",
        publisher="scripts-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Extension with scripts",
    )
    scripts = [
        ExtensionScriptsSchema(
            script_name="compile", script_command={"command": "tsc -p ./"}
        ),
        ExtensionScriptsSchema(
            script_name="watch", script_command={"command": "tsc -watch"}
        ),
    ]

    ext = create_extension(db_session, schema, scripts=scripts)

    assert ext.id is not None
    assert ext.name == "scripts-ext"
    assert len(ext.scripts) == 2


def test_create_extension_with_contributes(db_session: Session):
    """
    Test creating extension with contributes data.

    Verifies contributes and child tables are persisted and retrieved.
    """
    schema = ExtensionSchema(
        name="contrib-ext",
        publisher="contrib-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Extension with contributes",
    )
    contributes = ExtensionContributesSchema(
        configuration={"title": "Config"},
        keybindings=[
            ExtensionContributesKeybindingsSchema(
                key="ctrl+k", command="ext.hello", when="editorTextFocus"
            )
        ],
        menus=[
            ExtensionContributesMenusSchema(
                menu_location="editor/context", command="ext.hello"
            )
        ],
        authentication=[
            ExtensionContributesAuthenticationSchema(auth_id="github", label="GitHub")
        ],
        terminal=[
            ExtensionContributesTerminalSchema(
                profile_id="ext.term", title="Ext Terminal", icon="zap"
            )
        ],
        commands=[
            ExtensionContributesCommandsSchema(
                command_id="ext.hello", title="Hello", when="editorTextFocus"
            )
        ],
    )

    create_extension(db_session, schema, contributes=contributes)

    result = search_extension_by_name(db_session, "contrib-ext")
    assert result is not None
    assert result.contributes is not None
    assert result.contributes.configuration == {"title": "Config"}
    assert len(result.contributes.keybindings) == 1
    assert result.contributes.keybindings[0].command == "ext.hello"
    assert len(result.contributes.menus) == 1
    assert result.contributes.menus[0].menu_location == "editor/context"
    assert len(result.contributes.authentication) == 1
    assert result.contributes.authentication[0].auth_id == "github"
    assert len(result.contributes.terminal) == 1
    assert result.contributes.terminal[0].profile_id == "ext.term"
    assert len(result.contributes.commands) == 1
    assert result.contributes.commands[0].command_id == "ext.hello"
