from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from crud.crud import create_extension
from schemas.schemas import ExtensionSchema


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["Project"] == "Extrace"


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_search_extension_endpoint(client: TestClient, db_session: Session):
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
    response = client.get("/searchExtension?name=ghost")
    assert response.status_code == 404


def test_delete_extension_endpoint(client: TestClient, db_session: Session):
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
    mock_ext.web = None
    mock_ext.capabilities = None

    # Mock the service method to avoid filesystem scan
    with patch("routers.core.service.create_extension_by_name") as mock_create:
        mock_create.return_value = mock_ext

        response = client.post("/createExtension", json={"name": "new-ext"})

        assert response.status_code == 200
        assert response.json()["name"] == "new-ext"
        assert response.json()["id"] == 1
        mock_create.assert_called_once()


def test_create_extension_not_found(client: TestClient):
    """Test POST /createExtension when extension is missing on disk"""
    with patch("scanner.service.create_extension_by_name") as mock_create:
        mock_create.return_value = None

        response = client.post("/createExtension", json={"name": "ghost-ext"})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_create_extension_conflict(client: TestClient):
    """Test POST /createExtension when extension is duplicate"""
    with patch("scanner.service.create_extension_by_name") as mock_create:
        mock_create.side_effect = ValueError("Extension already exists")

        response = client.post("/createExtension", json={"name": "duplicate-ext"})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
