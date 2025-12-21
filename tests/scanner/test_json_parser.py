import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from scanner.json_parser import (
    get_package_json,
    parse_capabilities,
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


@patch("scanner.json_parser.Path")
@patch("scanner.json_parser.get_package_json")
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


@patch("scanner.json_parser.Path")
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
