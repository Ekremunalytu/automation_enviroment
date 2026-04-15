import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from workflows.extension_catalog.package_parser import (
    get_package_json,
    parse_capabilities,
    parse_contributes,
    parse_extra_fields,
    parse_npm_fields,
    parse_scripts,
    search_extension,
)

# Sample package.json content for testing
SAMPLE_PACKAGE_JSON = {
    "name": "test-ext",
    "publisher": "test-pub",
    "version": "1.0.0",
    "engines": {"vscode": "^1.0.0"},
    "dependencies": {"axios": "^1.0.0"},
    "devDependencies": {"typescript": "^5.0.0"},
    "extensionPack": ["ms-python.python", "ms-python.vscode-pylance"],
    "extensionDependencies": ["ms-vscode.cpptools"],
    "extensionKind": ["workspace"],
}


def test_get_package_json_success():
    """Test successful reading of package.json"""
    mock_path = MagicMock(spec=Path)
    mock_package_path = MagicMock(spec=Path)

    # Setup path behavior
    mock_path.__truediv__.return_value = mock_package_path
    mock_package_path.exists.return_value = True
    mock_package_path.is_file.return_value = True

    # Mock open() to return valid JSON
    with patch("builtins.open", mock_open(read_data=json.dumps(SAMPLE_PACKAGE_JSON))):
        result = get_package_json(mock_path)
        assert result == SAMPLE_PACKAGE_JSON


def test_get_package_json_not_found():
    """Test behavior when package.json does not exist"""
    mock_path = MagicMock(spec=Path)
    mock_package_path = MagicMock(spec=Path)

    mock_path.__truediv__.return_value = mock_package_path
    mock_package_path.exists.return_value = False

    result = get_package_json(mock_path)
    assert result is None


def test_get_package_json_invalid_json():
    """Test behavior with malformed JSON file"""
    mock_path = MagicMock(spec=Path)
    mock_package_path = MagicMock(spec=Path)

    # Setup path behavior
    mock_path.__truediv__.return_value = mock_package_path
    mock_package_path.exists.return_value = True
    mock_package_path.is_file.return_value = True

    # Mock open() to return INVALID JSON
    with patch("builtins.open", mock_open(read_data="{invalid-json")):
        result = get_package_json(mock_path)
        assert result is None


@patch("workflows.extension_catalog.manifest_reader.Path")
@patch("workflows.extension_catalog.manifest_reader.get_package_json")
def test_search_extension_found(mock_get_pkg, mock_path_cls):
    """Test successful extension search"""
    # Setup mock directory structure
    mock_root = MagicMock(spec=Path)
    mock_ext_dir = MagicMock(spec=Path)
    mock_ext_dir.is_dir.return_value = True

    mock_path_cls.return_value = mock_root
    mock_root.exists.return_value = True
    mock_root.is_dir.return_value = True
    mock_root.iterdir.return_value = [mock_ext_dir]

    # Setup get_package_json to return a match
    mock_get_pkg.return_value = SAMPLE_PACKAGE_JSON

    result = search_extension("test-ext")
    assert result == SAMPLE_PACKAGE_JSON


@patch("workflows.extension_catalog.manifest_reader.Path")
def test_search_extension_dir_not_found(mock_path_cls):
    """Test behavior when extensions directory is missing"""
    mock_root = MagicMock(spec=Path)
    mock_path_cls.return_value = mock_root
    mock_root.exists.return_value = False

    result = search_extension("any-ext")
    assert result is None


# =============================================================================
# Capabilities Parsing Tests
# =============================================================================


class TestParseCapabilities:
    """Tests for parse_capabilities function."""

    def test_no_capabilities_returns_none(self):
        """Test that missing capabilities field returns None."""
        package_json = {"name": "test", "version": "1.0.0"}
        result = parse_capabilities(package_json)
        assert result is None

    def test_empty_capabilities_returns_none(self):
        """Test that empty capabilities object returns None.

        An empty capabilities: {} block is treated as "no capabilities"
        since there's no useful data to store. This avoids creating
        database rows with all NULL values.
        """
        package_json = {"name": "test", "capabilities": {}}
        result = parse_capabilities(package_json)
        assert result is None

    def test_untrusted_workspaces_supported_true(self):
        """Test parsing untrustedWorkspaces with supported=true."""
        package_json = {"capabilities": {"untrustedWorkspaces": {"supported": True}}}
        result = parse_capabilities(package_json)
        assert result["untrusted_supported"] == "supported"

    def test_untrusted_workspaces_supported_false(self):
        """Test parsing untrustedWorkspaces with supported=false."""
        package_json = {"capabilities": {"untrustedWorkspaces": {"supported": False}}}
        result = parse_capabilities(package_json)
        assert result["untrusted_supported"] == "not_supported"

    def test_untrusted_workspaces_supported_limited(self):
        """Test parsing untrustedWorkspaces with supported='limited'."""
        package_json = {
            "capabilities": {
                "untrustedWorkspaces": {
                    "supported": "limited",
                    "description": "Some features disabled",
                    "restrictedConfigurations": ["python.path"],
                }
            }
        }
        result = parse_capabilities(package_json)
        assert result["untrusted_supported"] == "limited"
        assert result["untrusted_description"] == "Some features disabled"
        assert result["untrusted_restricted_configurations"] == ["python.path"]

    def test_untrusted_workspaces_boolean_shorthand(self):
        """Test parsing untrustedWorkspaces as simple boolean."""
        package_json = {"capabilities": {"untrustedWorkspaces": True}}
        result = parse_capabilities(package_json)
        assert result["untrusted_supported"] == "supported"

    def test_virtual_workspaces_supported_false(self):
        """Test parsing virtualWorkspaces with supported=false."""
        package_json = {
            "capabilities": {
                "virtualWorkspaces": {
                    "supported": False,
                    "description": "Needs filesystem",
                }
            }
        }
        result = parse_capabilities(package_json)
        assert result["virtual_supported"] == "not_supported"
        assert result["virtual_description"] == "Needs filesystem"

    def test_virtual_workspaces_boolean_shorthand(self):
        """Test parsing virtualWorkspaces as simple boolean."""
        package_json = {"capabilities": {"virtualWorkspaces": False}}
        result = parse_capabilities(package_json)
        assert result["virtual_supported"] == "not_supported"

    def test_full_capabilities_object(self):
        """Test parsing complete capabilities object."""
        package_json = {
            "capabilities": {
                "untrustedWorkspaces": {
                    "supported": "limited",
                    "description": "Limited in restricted mode",
                    "restrictedConfigurations": [
                        "python.defaultInterpreterPath",
                        "python.condaPath",
                    ],
                },
                "virtualWorkspaces": {
                    "supported": True,
                    "description": "Works in virtual workspaces",
                },
            }
        }
        result = parse_capabilities(package_json)

        assert result["untrusted_supported"] == "limited"
        assert result["untrusted_description"] == "Limited in restricted mode"
        assert len(result["untrusted_restricted_configurations"]) == 2
        assert result["virtual_supported"] == "supported"
        assert result["virtual_description"] == "Works in virtual workspaces"

    def test_invalid_support_value_returns_none(self):
        """Test that invalid support values return None."""
        package_json = {
            "capabilities": {"untrustedWorkspaces": {"supported": "invalid_value"}}
        }
        result = parse_capabilities(package_json)
        assert result["untrusted_supported"] is None


# =============================================================================
# Scripts Parsing Tests
# =============================================================================


class TestParseScripts:
    """Tests for parse_scripts function."""

    def test_no_scripts_returns_none(self):
        """Test that missing scripts field returns None."""
        package_json = {"name": "test", "version": "1.0.0"}
        result = parse_scripts(package_json)
        assert result is None

    def test_empty_scripts_returns_none(self):
        """Test that empty scripts object returns None."""
        package_json = {"name": "test", "scripts": {}}
        result = parse_scripts(package_json)
        assert result is None

    def test_scripts_not_dict_returns_none(self):
        """Test that non-dict scripts value returns None."""
        package_json = {"name": "test", "scripts": "invalid"}
        result = parse_scripts(package_json)
        assert result is None

    def test_parse_string_commands(self):
        """Test parsing scripts with string commands."""
        package_json = {
            "scripts": {
                "compile": "tsc -p ./",
                "watch": "tsc -watch -p ./",
                "test": "npm test",
            }
        }
        result = parse_scripts(package_json)

        assert result is not None
        assert len(result) == 3

        # Check first script
        compile_script = next(s for s in result if s["script_name"] == "compile")
        assert compile_script["script_command"] == {"command": "tsc -p ./"}

        # Check watch script
        watch_script = next(s for s in result if s["script_name"] == "watch")
        assert watch_script["script_command"] == {"command": "tsc -watch -p ./"}

    def test_parse_dict_commands(self):
        """Test parsing scripts with dict commands (complex format)."""
        package_json = {
            "scripts": {
                "build": {"command": "webpack", "args": ["--mode", "production"]},
            }
        }
        result = parse_scripts(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["script_name"] == "build"
        assert result[0]["script_command"] == {
            "command": "webpack",
            "args": ["--mode", "production"],
        }

    def test_skip_invalid_script_entries(self):
        """Test that invalid script entries (not str or dict) are skipped."""
        package_json = {
            "scripts": {
                "valid": "npm run valid",
                "invalid_int": 123,
                "invalid_list": ["a", "b"],
                "also_valid": "npm run also",
            }
        }
        result = parse_scripts(package_json)

        assert result is not None
        assert len(result) == 2
        script_names = [s["script_name"] for s in result]
        assert "valid" in script_names
        assert "also_valid" in script_names
        assert "invalid_int" not in script_names
        assert "invalid_list" not in script_names

    def test_all_invalid_scripts_returns_none(self):
        """Test that if all scripts are invalid, returns None."""
        package_json = {
            "scripts": {
                "invalid1": 123,
                "invalid2": ["list"],
                "invalid3": None,
            }
        }
        result = parse_scripts(package_json)
        assert result is None


# =============================================================================
# Activation Events Parsing Tests
# =============================================================================


class TestParseActivationEvents:
    """Tests for parse_activation_events function."""

    def test_no_activation_events_returns_none(self):
        """Test that missing activationEvents field returns None."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"name": "test", "version": "1.0.0"}
        result = parse_activation_events(package_json)
        assert result is None

    def test_empty_activation_events_returns_none(self):
        """Test that empty activationEvents array returns None."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"name": "test", "activationEvents": []}
        result = parse_activation_events(package_json)
        assert result is None

    def test_activation_events_not_list_returns_none(self):
        """Test that non-list activationEvents value returns None."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"name": "test", "activationEvents": "invalid"}
        result = parse_activation_events(package_json)
        assert result is None

    def test_parse_on_language_event(self):
        """Test parsing onLanguage activation event."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": ["onLanguage:python"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "onLanguage"
        assert result[0]["event_value"] == "python"

    def test_parse_on_command_event(self):
        """Test parsing onCommand activation event."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": ["onCommand:extension.activate"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "onCommand"
        assert result[0]["event_value"] == "extension.activate"

    def test_parse_star_event(self):
        """Test parsing * (startup) activation event."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": ["*"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "*"
        assert result[0]["event_value"] is None

    def test_parse_on_startup_finished(self):
        """Test parsing onStartupFinished activation event (no value)."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": ["onStartupFinished"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "onStartupFinished"
        assert result[0]["event_value"] is None

    def test_parse_workspace_contains_glob(self):
        """Test parsing workspaceContains with glob pattern."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": ["workspaceContains:**/.gitignore"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "workspaceContains"
        assert result[0]["event_value"] == "**/.gitignore"

    def test_parse_multiple_events(self):
        """Test parsing multiple activation events."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {
            "activationEvents": [
                "onLanguage:python",
                "onLanguage:javascript",
                "onCommand:extension.run",
                "*",
            ]
        }
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 4

        event_types = [e["event_type"] for e in result]
        assert event_types.count("onLanguage") == 2
        assert "onCommand" in event_types
        assert "*" in event_types

    def test_skip_invalid_event_entries(self):
        """Test that non-string activation events are skipped."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {
            "activationEvents": [
                "onLanguage:python",
                123,  # Invalid
                {"type": "onCommand"},  # Invalid
                "onCommand:test",
            ]
        }
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 2
        event_types = [e["event_type"] for e in result]
        assert "onLanguage" in event_types
        assert "onCommand" in event_types

    def test_all_invalid_events_returns_none(self):
        """Test that if all events are invalid, returns None."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        package_json = {"activationEvents": [123, None, {"invalid": True}]}
        result = parse_activation_events(package_json)
        assert result is None

    def test_event_with_multiple_colons(self):
        """Test that events with multiple colons are parsed correctly."""
        from workflows.extension_catalog.package_parser import parse_activation_events

        # The value part may contain colons (e.g., onUri)
        package_json = {"activationEvents": ["onUri:vscode://ext/path:with:colons"]}
        result = parse_activation_events(package_json)

        assert result is not None
        assert len(result) == 1
        assert result[0]["event_type"] == "onUri"
        assert result[0]["event_value"] == "vscode://ext/path:with:colons"


# =============================================================================
# Contributes Parsing Tests
# =============================================================================


class TestParseContributes:
    """Tests for parse_contributes function."""

    def test_no_contributes_returns_none(self):
        """Test that missing contributes field returns None."""
        package_json = {"name": "test", "version": "1.0.0"}
        result = parse_contributes(package_json)
        assert result is None

    def test_contributes_not_dict_returns_none(self):
        """Test that non-dict contributes value returns None."""
        package_json = {"contributes": ["invalid"]}
        result = parse_contributes(package_json)
        assert result is None

    def test_parse_contributes_children_and_jsonb_fields(self):
        """Test parsing contributes child arrays and JSONB fields."""
        package_json = {
            "contributes": {
                "keybindings": [
                    {
                        "key": "ctrl+k",
                        "command": "ext.hello",
                        "when": "editorTextFocus",
                    },
                    {"key": "ctrl+x"},
                ],
                "commands": [
                    {
                        "command": "ext.hello",
                        "title": "Hello",
                        "when": "editorTextFocus",
                    },
                    {"command": "ext.invalid"},
                ],
                "menus": {
                    "editor/context": [{"command": "ext.hello", "group": "navigation"}]
                },
                "authentication": [
                    {"id": "github", "label": "GitHub"},
                    {"id": "invalid"},
                ],
                "terminal": {
                    "profiles": [
                        {"id": "ext.term", "title": "Ext Terminal", "icon": "zap"},
                        {"id": "missing-title"},
                    ]
                },
                "configuration": {"title": "Test Config"},
                "snippets": [{"language": "python"}],
            }
        }

        result = parse_contributes(package_json)

        assert result is not None
        assert result["configuration"] == {"title": "Test Config"}
        assert result["snippets"] == [{"language": "python"}]

        assert len(result["keybindings"]) == 1
        keybinding = result["keybindings"][0]
        assert keybinding["key"] == "ctrl+k"
        assert keybinding["command"] == "ext.hello"
        assert keybinding["when"] == "editorTextFocus"

        assert len(result["commands"]) == 1
        command = result["commands"][0]
        assert command["command_id"] == "ext.hello"
        assert command["title"] == "Hello"

        assert len(result["menus"]) == 1
        menu = result["menus"][0]
        assert menu["menu_location"] == "editor/context"
        assert menu["command"] == "ext.hello"

        assert len(result["authentication"]) == 1
        auth = result["authentication"][0]
        assert auth["auth_id"] == "github"
        assert auth["label"] == "GitHub"

        assert len(result["terminal"]) == 1
        terminal = result["terminal"][0]
        assert terminal["profile_id"] == "ext.term"
        assert terminal["title"] == "Ext Terminal"


# =============================================================================
# NPM Fields Parsing Tests
# =============================================================================


class TestParseNpmFields:
    """Tests for parse_npm_fields function."""

    def test_parse_standard_npm_fields(self):
        """Test parsing standard npm fields."""
        package_json = {
            "name": "test",
            "repository": {"type": "git", "url": "git+https://github.com/a/b"},
            "author": "Me",
            "bugs": "https://bugs.com",
            "homepage": "https://home.com",
            # Unknown field
            "unknown": "value",
        }
        result = parse_npm_fields(package_json)

        assert result is not None
        assert result["repository"]["url"] == "git+https://github.com/a/b"
        assert result["author"] == "Me"
        assert result["bugs"] == "https://bugs.com"
        assert result["homepage"] == "https://home.com"
        assert "unknown" not in result
        assert "name" not in result  # processed separately

    def test_no_npm_fields_returns_none(self):
        """Test that missing npm fields returns None."""
        package_json = {
            "name": "test",
            "version": "1.0.0",
            # name/version are "known" db fields, not generic npm fields for this parser
        }
        result = parse_npm_fields(package_json)
        assert result is None


# =============================================================================
# Extra Fields Parsing Tests
# =============================================================================


class TestParseExtraFields:
    """Tests for parse_extra_fields function."""

    def test_parse_truly_extra_fields(self):
        """Test parsing fields that are neither standard npm nor vs code structure."""
        package_json = {
            "name": "test",
            "version": "1.0.0",
            # Standard fields (ignored)
            "repository": "repo",
            "scripts": {},
            # Extra fields (collected)
            "myCustomConfig": {"a": 1},
            "__metadata": "xyz",
        }
        result = parse_extra_fields(package_json)

        assert result is not None
        assert "myCustomConfig" in result
        assert result["myCustomConfig"] == {"a": 1}
        assert "__metadata" in result
        assert result["__metadata"] == "xyz"

        # Check ignored fields
        assert "name" not in result
        assert "version" not in result
        assert "repository" not in result
        assert "scripts" not in result

    def test_no_extra_fields_returns_none(self):
        """Test that having only known fields returns None."""
        package_json = {
            "name": "test",
            "version": "1.0.0",
            "publisher": "pub",
            "engines": {},
            "scripts": {},
            "activationEvents": [],
            "contributes": {},
            "repository": "repo",
        }
        result = parse_extra_fields(package_json)
        assert result is None
