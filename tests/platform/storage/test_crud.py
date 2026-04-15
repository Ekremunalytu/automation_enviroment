from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage.crud import (
    create_extension,
    delete_extension,
    get_db_extensions_base_info,
    get_extension_activation_events,
    get_extension_by_id,
    get_extension_capabilities,
    get_extension_contributes_all,
    get_extension_contributes_commands,
    get_extension_scripts,
    get_extensions_all_info,
    search_extension_by_name,
)
from appcore.contracts.schemas import (
    ExtensionActivationEventsSchema,
    ExtensionCapabilitiesSchema,
    ExtensionContributesAuthenticationSchema,
    ExtensionContributesCommandsSchema,
    ExtensionContributesKeybindingsSchema,
    ExtensionContributesMenusSchema,
    ExtensionContributesSchema,
    ExtensionContributesTerminalSchema,
    ExtensionSchema,
    ExtensionScriptsSchema,
)

pytestmark = pytest.mark.requires_db


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


def test_create_extension_with_extra_info(db_session: Session):
    """
    Test creating extension with npm_fields and extra_fields.

    Verifies that flexible JSONB fields are correctly parsed, stored,
    and retrieved.
    """
    schema = ExtensionSchema(
        name="extra-ext",
        publisher="extra-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
        description="Extension with extra fields",
        npm_fields={
            "repository": {"type": "git", "url": "https://github.com/test/repo"},
            "author": {"name": "Test Author"},
        },
        extra_fields={
            "customConfig": {"enabled": True},
            "unknownField": "some-value",
        },
    )

    ext = create_extension(db_session, schema)

    assert ext.id is not None
    assert ext.name == "extra-ext"
    assert ext.npm_fields["repository"]["url"] == "https://github.com/test/repo"
    assert ext.npm_fields["author"]["name"] == "Test Author"
    assert ext.extra_fields["customConfig"]["enabled"] is True
    assert ext.extra_fields["unknownField"] == "some-value"


def test_get_extension_by_id_found_and_not_found(db_session: Session):
    """Test primary key lookup for existing and missing records."""
    schema = ExtensionSchema(
        name="id-ext",
        publisher="id-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    ext = create_extension(db_session, schema)

    found = get_extension_by_id(db_session, ext.id)
    assert found is not None
    assert found.name == "id-ext"
    assert get_extension_by_id(db_session, ext.id + 9999) is None


def test_search_extension_with_filters_and_ambiguous_result(db_session: Session):
    """Test ambiguous search handling and filtered exact search."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="multi-ext",
            publisher="pub-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="multi-ext",
            publisher="pub-b",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )

    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        search_extension_by_name(db_session, "multi-ext")

    result = search_extension_by_name(
        db_session, "multi-ext", publisher="pub-b", version="2.0.0"
    )
    assert result is not None
    assert result.publisher == "pub-b"
    assert result.version == "2.0.0"


def test_create_extension_with_capabilities(db_session: Session):
    """Test creating extension with capabilities relationship."""
    schema = ExtensionSchema(
        name="caps-ext",
        publisher="caps-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    capabilities = ExtensionCapabilitiesSchema(
        untrusted_supported="supported",
        untrusted_description="Restricted mode works",
        virtual_supported="limited",
        virtual_description="Virtual FS partially supported",
    )

    ext = create_extension(db_session, schema, capabilities=capabilities)
    assert ext.capabilities is not None
    assert str(ext.capabilities.untrusted_supported) == "supported"
    assert str(ext.capabilities.virtual_supported) == "limited"


def test_create_extension_rolls_back_on_sqlalchemy_error(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    """Test rollback behavior when commit raises SQLAlchemyError."""
    schema = ExtensionSchema(
        name="rollback-ext",
        publisher="rollback-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )

    rollback_spy = MagicMock(wraps=db_session.rollback)
    monkeypatch.setattr(db_session, "rollback", rollback_spy)
    monkeypatch.setattr(
        db_session,
        "commit",
        MagicMock(side_effect=SQLAlchemyError("simulated db failure")),
    )

    with pytest.raises(SQLAlchemyError, match="simulated db failure"):
        create_extension(db_session, schema)

    assert rollback_spy.call_count == 1


def test_get_extensions_all_info_applies_skip_and_limit(db_session: Session):
    """Test pagination arguments in full info query."""
    for idx in range(3):
        create_extension(
            db_session,
            ExtensionSchema(
                name=f"paged-ext-{idx}",
                publisher="paged-pub",
                version=f"1.0.{idx}",
                engines={"vscode": "^1.0.0"},
            ),
        )

    paged = get_extensions_all_info(db_session, skip=1, limit=1)
    assert len(paged) == 1


def test_get_db_extensions_base_info_returns_data(db_session: Session):
    """Test base info query returns created extensions."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="base-ext",
            publisher="base-pub",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
            description="base info",
        ),
    )

    rows = get_db_extensions_base_info(db_session)
    assert any(row.name == "base-ext" for row in rows)


def test_delete_extension_with_filters_and_ambiguous_result(db_session: Session):
    """Test delete ambiguity detection and filtered delete path."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="dup-delete",
            publisher="pub-1",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="dup-delete",
            publisher="pub-2",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )

    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        delete_extension(db_session, "dup-delete")

    assert (
        delete_extension(
            db_session,
            "dup-delete",
            publisher="pub-2",
            version="2.0.0",
        )
        is True
    )
    assert search_extension_by_name(db_session, "dup-delete", "pub-2", "2.0.0") is None
    assert (
        search_extension_by_name(db_session, "dup-delete", "pub-1", "1.0.0") is not None
    )


def test_get_extension_scripts_with_filters_and_not_found(db_session: Session):
    """Test scripts retrieval with filters and missing extension path."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="scripts-filtered",
            publisher="scripts-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        scripts=[
            ExtensionScriptsSchema(
                script_name="build",
                script_command={"command": "npm run build"},
            )
        ],
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="scripts-filtered",
            publisher="scripts-b",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        scripts=[
            ExtensionScriptsSchema(
                script_name="test",
                script_command={"command": "npm run test"},
            )
        ],
    )

    scripts = get_extension_scripts(
        db_session,
        "scripts-filtered",
        publisher="scripts-b",
        version="2.0.0",
    )
    assert scripts is not None
    assert len(scripts) == 1
    assert scripts[0].script_name == "test"
    assert get_extension_scripts(db_session, "ghost-ext") is None


def test_relation_helpers_raise_for_ambiguous_extension_name(db_session: Session):
    """Relation lookups should reject ambiguous name-only matches."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="ambiguous-relations",
            publisher="pub-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        scripts=[
            ExtensionScriptsSchema(
                script_name="build",
                script_command={"command": "npm run build"},
            )
        ],
        activation_events=[
            ExtensionActivationEventsSchema(
                event_type="onLanguage",
                event_value="python",
            )
        ],
        capabilities=ExtensionCapabilitiesSchema(untrusted_supported="supported"),
        contributes=ExtensionContributesSchema(
            commands=[
                ExtensionContributesCommandsSchema(
                    command_id="ext.run",
                    title="Run",
                )
            ]
        ),
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="ambiguous-relations",
            publisher="pub-b",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )

    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        get_extension_scripts(db_session, "ambiguous-relations")
    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        get_extension_activation_events(db_session, "ambiguous-relations")
    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        get_extension_capabilities(db_session, "ambiguous-relations")
    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        get_extension_contributes_all(db_session, "ambiguous-relations")
    with pytest.raises(ValueError, match="Multiple extensions match this name"):
        get_extension_contributes_commands(db_session, "ambiguous-relations")


def test_get_extension_activation_events_with_filters_and_not_found(
    db_session: Session,
):
    """Test activation event retrieval with exact filters and missing path."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="events-filtered",
            publisher="events-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        activation_events=[
            ExtensionActivationEventsSchema(
                event_type="onLanguage",
                event_value="python",
            )
        ],
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="events-filtered",
            publisher="events-b",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        activation_events=[
            ExtensionActivationEventsSchema(
                event_type="onCommand",
                event_value="ext.run",
            )
        ],
    )

    events = get_extension_activation_events(
        db_session,
        extension_name="events-filtered",
        extension_publisher="events-b",
        extension_version="2.0.0",
    )
    assert events is not None
    assert len(events) == 1
    assert events[0].event_type == "onCommand"
    assert get_extension_activation_events(db_session, "missing-events") is None


def test_get_extension_capabilities_with_filters_and_not_found(db_session: Session):
    """Test capabilities retrieval for found and missing extensions."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="caps-filtered",
            publisher="caps-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        capabilities=ExtensionCapabilitiesSchema(
            untrusted_supported="supported",
        ),
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="caps-no-data",
            publisher="caps-a",
            version="1.0.1",
            engines={"vscode": "^1.0.0"},
        ),
    )

    caps = get_extension_capabilities(
        db_session,
        extension_name="caps-filtered",
        extension_publisher="caps-a",
        extension_version="1.0.0",
    )
    assert caps is not None
    assert str(caps.untrusted_supported) == "supported"
    assert get_extension_capabilities(db_session, "missing-caps") is None
    assert (
        get_extension_capabilities(
            db_session,
            extension_name="caps-no-data",
            extension_publisher="caps-a",
            extension_version="1.0.1",
        )
        is None
    )


def test_get_extension_contributes_all_with_filters_and_not_found(db_session: Session):
    """Test contributes retrieval with filtered lookup and missing path."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="contrib-filtered",
            publisher="contrib-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        contributes=ExtensionContributesSchema(
            configuration={"title": "Contrib"},
            commands=[
                ExtensionContributesCommandsSchema(
                    command_id="contrib.hello",
                    title="Hello",
                )
            ],
        ),
    )

    contributes = get_extension_contributes_all(
        db_session,
        extension_name="contrib-filtered",
        extension_publisher="contrib-a",
        extension_version="1.0.0",
    )
    assert contributes is not None
    assert contributes.configuration == {"title": "Contrib"}
    assert get_extension_contributes_all(db_session, "missing-contrib") is None


def test_get_extension_contributes_commands_none_empty_and_populated(
    db_session: Session,
):
    """Test contributes command retrieval for all return shapes."""
    create_extension(
        db_session,
        ExtensionSchema(
            name="no-contrib-commands",
            publisher="cmd-a",
            version="1.0.0",
            engines={"vscode": "^1.0.0"},
        ),
    )
    create_extension(
        db_session,
        ExtensionSchema(
            name="with-contrib-commands",
            publisher="cmd-a",
            version="2.0.0",
            engines={"vscode": "^1.0.0"},
        ),
        contributes=ExtensionContributesSchema(
            commands=[
                ExtensionContributesCommandsSchema(
                    command_id="cmd.run",
                    title="Run",
                )
            ]
        ),
    )

    assert get_extension_contributes_commands(db_session, "missing-cmds") is None
    assert (
        get_extension_contributes_commands(
            db_session,
            extension_name="no-contrib-commands",
            extension_publisher="cmd-a",
            extension_version="1.0.0",
        )
        == []
    )

    commands = get_extension_contributes_commands(
        db_session,
        extension_name="with-contrib-commands",
        extension_publisher="cmd-a",
        extension_version="2.0.0",
    )
    assert commands is not None
    assert len(commands) == 1
    assert commands[0].command_id == "cmd.run"
