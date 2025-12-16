import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from scanner.json_parser import get_package_json, search_extension

# Sample package.json content for testing
SAMPLE_PACKAGE_JSON = {
    "name": "test-ext",
    "publisher": "test-pub",
    "version": "1.0.0",
    "engines": {"vscode": "^1.0.0"},
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
