from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import ExtensionSchema
from appcore.storage.crud import create_extension


def _build_validation_error() -> ValidationError:
    try:
        ExtensionSchema(name="invalid-only")
    except ValidationError as exc:
        return exc
    raise AssertionError("Expected ExtensionSchema validation to fail")


def test_read_root(client: TestClient):
    """Test the root endpoint returns project info."""
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["Project"] == settings.project.NAME
    assert payload["Version"] == settings.project.VERSION


def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == settings.api.HEALTH_STATUS


def test_search_extension_endpoint(client: TestClient, db_session: Session):
    """Test searching for an existing extension."""
    # Setup
    schema = ExtensionSchema(
        name="api-test",
        publisher="api-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    create_extension(db_session, schema)

    # Test
    response = client.get("/searchExtension?name=api-test")
    assert response.status_code == 200
    assert response.json()["name"] == "api-test"


def test_search_extension_not_found(client: TestClient):
    """Test searching for a non-existent extension returns 404."""
    response = client.get("/searchExtension?name=ghost")
    assert response.status_code == 404


def test_delete_extension_endpoint(client: TestClient, db_session: Session):
    """Test deleting an extension via API."""
    # Setup
    schema = ExtensionSchema(
        name="delete-api",
        publisher="del-pub",
        version="1.0.0",
        engines={"vscode": "^1.0.0"},
    )
    create_extension(db_session, schema)

    # Test
    response = client.delete("/deleteExtension?name=delete-api")
    assert response.status_code == 200

    # Verify deletion
    response = client.get("/searchExtension?name=delete-api")
    assert response.status_code == 404


def test_create_extension_endpoint(client: TestClient, db_session: Session):
    """Test POST /createExtension with mocked service"""
    # Create a mock Extension ORM object (not schema)
    mock_ext = MagicMock()
    mock_ext.id = 1
    mock_ext.name = "new-ext"
    mock_ext.publisher = "new-pub"
    mock_ext.version = "2.0.0"
    mock_ext.engines = {"vscode": "^1.0.0"}
    mock_ext.license = None
    mock_ext.displayName = None
    mock_ext.description = None
    mock_ext.categories = None
    mock_ext.keywords = None
    mock_ext.galleryBanner = None
    mock_ext.preview = None
    mock_ext.badges = None
    mock_ext.markdown = None
    mock_ext.qna = None
    mock_ext.sponsor = None
    mock_ext.icon = None
    mock_ext.pricing = None
    mock_ext.main = None
    mock_ext.browser = None
    mock_ext.dependencies = None
    mock_ext.devDependencies = None
    mock_ext.capabilities = None
    mock_ext.activation_events = []
    mock_ext.scripts = []
    mock_ext.contributes = None
    mock_ext.npm_fields = None
    mock_ext.extra_fields = None
    mock_ext.extensionPack = []
    mock_ext.extensionDependencies = []
    mock_ext.extensionKind = []

    # Mock the service method to avoid filesystem scan
    with patch(
        "workflows.extension_catalog.router.service.create_extension_by_name"
    ) as mock_create:
        mock_create.return_value = mock_ext

        response = client.post("/createExtension", json={"name": "new-ext"})

        assert response.status_code == 200
        assert response.json()["name"] == "new-ext"
        assert response.json()["id"] == 1
        mock_create.assert_called_once()


def test_get_extensions_all_info_with_pagination(client: TestClient):
    """Test GET /getExtensionsAllInfo with pagination params."""
    with patch(
        "workflows.extension_catalog.router.service.get_all_extensions_all"
    ) as mock_get:
        mock_get.return_value = []

        response = client.get("/getExtensionsAllInfo?skip=5&limit=10")

        assert response.status_code == 200
        assert response.json() == []
        _, kwargs = mock_get.call_args
        assert kwargs["skip"] == 5
        assert kwargs["limit"] == 10


def test_create_extension_not_found(client: TestClient):
    """Test POST /createExtension when extension is missing on disk"""
    with patch(
        "workflows.extension_catalog.service.create_extension_by_name"
    ) as mock_create:
        mock_create.return_value = None

        response = client.post("/createExtension", json={"name": "ghost-ext"})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_create_extension_conflict(client: TestClient):
    """Test POST /createExtension when extension is duplicate"""
    with patch(
        "workflows.extension_catalog.service.create_extension_by_name"
    ) as mock_create:
        mock_create.side_effect = ValueError("Extension already exists")

        response = client.post("/createExtension", json={"name": "duplicate-ext"})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


def test_get_extension_scripts(client: TestClient):
    """Test GET /getExtensionScripts"""
    mock_scripts = [{"script_name": "test", "script_command": {"command": "echo test"}}]
    with patch(
        "workflows.extension_catalog.router.service.get_extension_scripts"
    ) as mock_get:
        mock_get.return_value = mock_scripts

        response = client.get("/getExtensionScripts?name=test-ext")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["script_name"] == "test"
        mock_get.assert_called_once()


def test_get_extension_activation_events(client: TestClient):
    """Test GET /getExtensionActivationEvents"""
    mock_events = [{"event_type": "onLanguage", "event_value": "python"}]
    with patch(
        "workflows.extension_catalog.router.service.get_extension_activation_events"
    ) as mock_get:
        mock_get.return_value = mock_events

        response = client.get("/getExtensionActivationEvents?name=test-ext")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["event_type"] == "onLanguage"
        mock_get.assert_called_once()


def test_get_extension_scripts_not_found(client: TestClient):
    """Test GET /getExtensionScripts returns 404 when not found"""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_scripts"
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/getExtensionScripts?name=ghost-ext")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_extension_activation_events_not_found(client: TestClient):
    """Test GET /getExtensionActivationEvents returns 404 when not found"""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_activation_events"
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/getExtensionActivationEvents?name=ghost-ext")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_extension_capabilities(client: TestClient):
    """Test GET /getExtensionCapabilities success case."""
    mock_caps = {
        "untrusted_supported": "limited",
        "virtual_supported": "not_supported",
    }
    with patch(
        "workflows.extension_catalog.router.service.get_extension_capabilites"
    ) as mock_get:
        mock_get.return_value = mock_caps

        response = client.get("/getExtensionCapabilities?name=test-ext")

        assert response.status_code == 200
        assert response.json()["untrusted_supported"] == "limited"
        mock_get.assert_called_once()


def test_get_extension_capabilities_not_found(client: TestClient):
    """Test GET /getExtensionCapabilities returns 404 when not found."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_capabilites"
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/getExtensionCapabilities?name=ghost-ext")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# =============================================================================
# Exception / Error Handling Tests
# =============================================================================


def test_search_extension_error_handling(client: TestClient):
    """Test search endpoint database error handling."""
    with patch(
        "workflows.extension_catalog.router.service.search_extension_by_name",
        side_effect=SQLAlchemyError("DB Error"),
    ):
        response = client.get("/searchExtension?name=boom")
        assert response.status_code == 500
        assert "Database operation failed" in response.json()["detail"]


def test_create_extension_conflict_error(client: TestClient):
    """Duplicate create attempts should still map to 409."""
    with patch(
        "workflows.extension_catalog.router.service.create_extension_by_name",
        side_effect=ValueError("Invalid Data"),
    ):
        response = client.post("/createExtension", json={"name": "bad-ext"})
        assert response.status_code == 409  # ValueError maps to 409 in create
        assert "Invalid Data" in response.json()["detail"]


def test_create_extension_validation_error(client: TestClient):
    """Manifest validation errors should be returned as 422 details."""
    with patch(
        "workflows.extension_catalog.router.service.create_extension_by_name",
        side_effect=_build_validation_error(),
    ):
        response = client.post("/createExtension", json={"name": "bad-manifest"})
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "missing"


def test_delete_extension_validation_error(client: TestClient):
    """Test delete endpoint validation error."""
    with patch(
        "workflows.extension_catalog.router.service.delete_extension_by_name",
        side_effect=ValueError("Cannot delete"),
    ):
        response = client.delete("/deleteExtension?name=bad-ext")
        assert response.status_code == 400
        assert "Cannot delete" in response.json()["detail"]


def test_delete_extension_database_error(client: TestClient):
    """Test delete endpoint database error mapping."""
    with patch(
        "workflows.extension_catalog.router.service.delete_extension_by_name",
        side_effect=SQLAlchemyError("Boom"),
    ):
        response = client.delete("/deleteExtension?name=boom")
        assert response.status_code == 500
        assert "Database operation failed" in response.json()["detail"]


def test_get_base_info_value_error(client: TestClient):
    """Test get base info validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_all_extensions_basic",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionsBaseInfo")
        assert response.status_code == 400
        assert "Bad" in response.json()["detail"]


def test_get_base_info_database_error(client: TestClient):
    """Test get base info database error."""
    with patch(
        "workflows.extension_catalog.router.service.get_all_extensions_basic",
        side_effect=SQLAlchemyError("Boom"),
    ):
        response = client.get("/getExtensionsBaseInfo")
        assert response.status_code == 500
        assert "Database operation failed" in response.json()["detail"]


def test_get_all_info_value_error(client: TestClient):
    """Test get all info validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_all_extensions_all",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionsAllInfo")
        assert response.status_code == 400


def test_get_all_info_database_error(client: TestClient):
    """Test get all info database error."""
    with patch(
        "workflows.extension_catalog.router.service.get_all_extensions_all",
        side_effect=SQLAlchemyError("Boom"),
    ):
        response = client.get("/getExtensionsAllInfo")
        assert response.status_code == 500
        assert "Database operation failed" in response.json()["detail"]


def test_extension_scripts_value_error(client: TestClient):
    """Test get scripts validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_scripts",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionScripts?name=bad")
        assert response.status_code == 400


def test_activation_events_value_error(client: TestClient):
    """Test get activation events validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_activation_events",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionActivationEvents?name=bad")
        assert response.status_code == 400


def test_extension_capabilities_value_error(client: TestClient):
    """Test get capabilities validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_capabilites",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionCapabilities?name=bad")
        assert response.status_code == 400


# =============================================================================
# Extension Contributes Tests
# =============================================================================


def test_get_extension_contributes_all(client: TestClient):
    """Test GET /getExtensionContributesAll success case."""
    mock_contributes = {
        "configuration": {"title": "Test Config"},
        "commands": [],
        "keybindings": [],
        "menus": [],
        "authentication": [],
        "terminal": [],
    }
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_all"
    ) as mock_get:
        mock_get.return_value = mock_contributes

        response = client.get("/getExtensionContributesAll?name=test-ext")

        assert response.status_code == 200
        assert response.json()["configuration"] == {"title": "Test Config"}
        mock_get.assert_called_once()


def test_get_extension_contributes_all_not_found(client: TestClient):
    """Test GET /getExtensionContributesAll returns 404 when not found."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_all"
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/getExtensionContributesAll?name=ghost-ext")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_extension_contributes_all_value_error(client: TestClient):
    """Test GET /getExtensionContributesAll validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_all",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionContributesAll?name=bad")
        assert response.status_code == 400


def test_get_extension_contributes_commands(client: TestClient):
    """Test GET /getExtensionContributesCommands success case."""
    mock_commands = [
        {"command_id": "ext.hello", "title": "Hello World"},
        {"command_id": "ext.goodbye", "title": "Goodbye World"},
    ]
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_commands"
    ) as mock_get:
        mock_get.return_value = mock_commands

        response = client.get("/getExtensionContributesCommands?name=test-ext")

        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["command_id"] == "ext.hello"
        mock_get.assert_called_once()


def test_get_extension_contributes_commands_not_found(client: TestClient):
    """Test GET /getExtensionContributesCommands returns 404 when not found."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_commands"
    ) as mock_get:
        mock_get.return_value = None

        response = client.get("/getExtensionContributesCommands?name=ghost-ext")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_get_extension_contributes_commands_empty(client: TestClient):
    """Test GET /getExtensionContributesCommands returns empty list."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_commands"
    ) as mock_get:
        mock_get.return_value = []

        response = client.get("/getExtensionContributesCommands?name=no-commands")

        assert response.status_code == 200
        assert response.json() == []


def test_get_extension_contributes_commands_value_error(client: TestClient):
    """Test GET /getExtensionContributesCommands validation error."""
    with patch(
        "workflows.extension_catalog.router.service.get_extension_contributes_commands",
        side_effect=ValueError("Bad"),
    ):
        response = client.get("/getExtensionContributesCommands?name=bad")
        assert response.status_code == 400
