"""
Tests for Marketplace Router
=============================

Tests for /api/marketplace/search and /api/marketplace/download endpoints.
All external calls (HTTP + DB writes) are mocked via unittest.mock.patch.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from executor.host import ExecutorError
from workflows.extension_catalog.manifest_reader import PackageJsonReadError
from workflows.marketplace import (
    analysis_service,
    router as marketplace_router,
    trigger_service,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SEARCH_RESULTS = [
    {
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "displayName": "Python",
        "description": "Python language support.",
        "installs": 100_000_000,
        "rating": 4.8,
    }
]

SAMPLE_DOWNLOAD_RESPONSE = {
    "status": "success",
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
    "extension_dir": "/app/extensions/ms-python.python-2025.0.0",
    "db_id": 42,
    "message": (
        "Extension ms-python.python@2025.0.0 downloaded and analyzed successfully."
    ),
}


# ---------------------------------------------------------------------------
# Search Tests
# ---------------------------------------------------------------------------


def test_search_success(client: TestClient) -> None:
    """Normal search returns 200 with a list of extensions."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=SAMPLE_SEARCH_RESULTS,
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "python"
    assert data[0]["publisher"] == "ms-python"
    assert data[0]["installs"] == 100_000_000


def test_search_empty_query(client: TestClient) -> None:
    """Empty query string returns 400."""
    response = client.get("/api/marketplace/search", params={"query": ""})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_whitespace_query(client: TestClient) -> None:
    """Whitespace-only query string returns 400."""
    response = client.get("/api/marketplace/search", params={"query": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_upstream_error(client: TestClient) -> None:
    """httpx.HTTPError from marketplace client results in 502."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        side_effect=httpx.HTTPStatusError(
            "Bad Gateway", request=MagicMock(), response=MagicMock()
        ),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502
    assert "Marketplace API unavailable" in response.json()["detail"]


def test_search_network_error(client: TestClient) -> None:
    """httpx.ConnectError (subclass of HTTPError) from marketplace client results in 502."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.get("/api/marketplace/search", params={"query": "python"})

    assert response.status_code == 502


def test_search_page_size_clamp_low(client: TestClient) -> None:
    """page_size=0 is clamped to 1 (no error raised)."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ) as mock_search:
        response = client.get(
            "/api/marketplace/search", params={"query": "test", "page_size": 0}
        )

    assert response.status_code == 200
    # Verify clamped value was passed (1, not 0)
    mock_search.assert_called_once_with("test", 1)


def test_search_page_size_clamp_high(client: TestClient) -> None:
    """page_size=500 is clamped to 100."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ) as mock_search:
        response = client.get(
            "/api/marketplace/search", params={"query": "test", "page_size": 500}
        )

    assert response.status_code == 200
    mock_search.assert_called_once_with("test", 100)


def test_search_returns_empty_list(client: TestClient) -> None:
    """Scanner returning [] is a valid 200 response."""
    with patch(
        "workflows.marketplace.client.search_marketplace",
        return_value=[],
    ):
        response = client.get(
            "/api/marketplace/search", params={"query": "zzznoresults"}
        )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Download Tests
# ---------------------------------------------------------------------------


def _mock_extension(db_id: int = 42) -> MagicMock:
    """Build a mock ORM Extension object."""
    ext = MagicMock()
    ext.id = db_id
    return ext


def test_download_success(client: TestClient) -> None:
    """Successful download returns 200 with db_id."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            return_value=_mock_extension(42),
        ) as mock_create,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["db_id"] == 42
    assert data["publisher"] == "ms-python"
    assert data["name"] == "python"
    assert data["version"] == "2025.0.0"
    mock_create.assert_called_once_with(
        ANY,
        ext_path,
        expected_name="python",
        expected_publisher="ms-python",
        expected_version="2025.0.0",
    )


def test_download_duplicate_returns_existing_extension(client: TestClient) -> None:
    """Duplicate catalog insert should still return a usable download response."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=ValueError("Duplicate entry"),
        ),
        patch(
            "workflows.marketplace.router.search_extension_by_name",
            return_value=_mock_extension(42),
        ) as mock_search,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["db_id"] == 42
    assert "already downloaded" in data["message"]
    mock_search.assert_called_once_with(
        ANY,
        "python",
        extension_publisher="ms-python",
        extension_version="2025.0.0",
    )


def test_download_duplicate_without_existing_record_returns_409(
    client: TestClient,
) -> None:
    """Keep the conflict response if the duplicate cannot be resolved to a stored extension."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=ValueError("Duplicate entry"),
        ),
        patch(
            "workflows.marketplace.router.search_extension_by_name",
            return_value=None,
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_download_missing_manifest_returns_specific_500(client: TestClient) -> None:
    """Missing package.json should surface a diagnostic 500 detail."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=PackageJsonReadError.missing(ext_path / "package.json"),
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 500
    assert "package.json is missing" in response.json()["detail"]


def test_download_invalid_manifest_returns_specific_500(client: TestClient) -> None:
    """Invalid package.json should surface a parse-specific 500 detail."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=PackageJsonReadError.invalid_json(
                ext_path / "package.json",
                "Expecting property name enclosed in double quotes",
            ),
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 500
    assert "contains invalid JSON" in response.json()["detail"]


def test_download_manifest_mismatch_returns_502(client: TestClient) -> None:
    """Manifest mismatch from downloaded VSIX should surface as upstream failure."""
    ext_path = Path("/app/extensions/ms-python.python-2025.0.0")

    with (
        patch(
            "workflows.marketplace.client.download_and_extract_vsix",
            return_value=ext_path,
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            side_effect=marketplace_router.ExtensionManifestMismatchError(
                "Downloaded extension metadata does not match the requested artifact."
            ),
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 502
    assert "does not match" in response.json()["detail"]


def test_download_network_error_502(client: TestClient) -> None:
    """httpx.HTTPError during VSIX download → 502."""
    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 502
    assert "Failed to download" in response.json()["detail"]


def test_download_missing_publisher_422(client: TestClient) -> None:
    """Missing required field 'publisher' → 422 Unprocessable Entity."""
    response = client.post(
        "/api/marketplace/download",
        json={"name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_missing_name_422(client: TestClient) -> None:
    """Missing required field 'name' → 422."""
    response = client.post(
        "/api/marketplace/download",
        json={"publisher": "ms-python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_empty_publisher_422(client: TestClient) -> None:
    """Empty string for 'publisher' (min_length=1) → 422."""
    response = client.post(
        "/api/marketplace/download",
        json={"publisher": "", "name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422


def test_download_http_status_error_502(client: TestClient) -> None:
    """httpx.HTTPStatusError during download → 502."""
    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        ),
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "nonexistent",
                "name": "nonexistent",
                "version": "0.0.0",
            },
        )

    assert response.status_code == 502


# ---------------------------------------------------------------------------
# Analyze Tests
# ---------------------------------------------------------------------------

ANALYZE_PAYLOAD = {
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
}


def _vsix_path_exists(exists: bool = True):
    """Return a mock Path whose .exists() returns the given value."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    mock_path.name = "ms-python.python-2025.0.0.vsix"
    return mock_path


def test_analyze_success(client: TestClient) -> None:
    """Successful analyze returns 200 with install and automation output."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="Extension installed successfully.",
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="Automation completed.",
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["install_output"] == "Extension installed successfully."
    assert data["automation_output"] == "Automation completed."
    assert data["report_path"].startswith(
        "activation_report_ms-python.python-2025.0.0-"
    )
    assert data["report_path"].endswith(".json")


def test_build_trigger_payload_skips_when_explicit_scenario_is_set() -> None:
    """Explicit scenarios should bypass smart trigger selection entirely."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD, scenario="demo")

    trigger_path, scenarios, message = trigger_service.build_trigger_payload(
        db=MagicMock(),
        request=request,
    )

    assert trigger_path is None
    assert scenarios == []
    assert "skipped" in message.lower()


def test_build_trigger_payload_returns_default_when_no_activation_events() -> None:
    """Missing activation metadata should fall back to the default flow."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)

    with (
        patch(
            "workflows.marketplace.trigger_service.get_extension_activation_events",
            return_value=[],
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_contributes_all",
            return_value=None,
        ),
    ):
        trigger_path, scenarios, message = trigger_service.build_trigger_payload(
            db=MagicMock(),
            request=request,
        )

    assert trigger_path is None
    assert scenarios == []
    assert "default sandbox flow" in message.lower()


def test_build_trigger_payload_passes_commands_and_custom_editors() -> None:
    """Smart trigger selection should receive parsed commands and custom editors."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    activation_events = [
        SimpleNamespace(event_type="onCommand", event_value="extension.run")
    ]
    contributes = SimpleNamespace(
        customEditors=[{"viewType": "custom.editor"}],
        authentication=[{"auth_id": "github", "label": "GitHub"}],
        views={"explorer": [{"id": "webview.sample"}]},
        commands=[SimpleNamespace(title="Run", command_id="extension.run")],
    )
    payload = SimpleNamespace(selected_scenarios=["command_palette"])

    with (
        patch(
            "workflows.marketplace.trigger_service.get_extension_activation_events",
            return_value=activation_events,
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_contributes_all",
            return_value=contributes,
        ),
        patch(
            "workflows.marketplace.trigger_service.select_scenarios",
            return_value=payload,
        ) as mock_select,
        patch(
            "workflows.marketplace.trigger_service.write_trigger_file",
            return_value="/results/triggers.json",
        ) as mock_write,
    ):
        trigger_path, scenarios, message = trigger_service.build_trigger_payload(
            db=MagicMock(),
            request=request,
        )

    assert trigger_path == "/results/triggers.json"
    assert scenarios == ["command_palette"]
    assert "trigger requested for ms-python.python" in message.lower()
    assert "/results/triggers.json" in message
    mock_select.assert_called_once_with(
        [{"event_type": "onCommand", "event_value": "extension.run"}],
        [{"viewType": "custom.editor"}],
        "ms-python.python",
        contributes_commands=[{"title": "Run", "command_id": "extension.run"}],
        contributes_authentication=[{"auth_id": "github", "label": "GitHub"}],
        contributes_views={"explorer": [{"id": "webview.sample"}]},
        contributes_debuggers=None,
        contributes_walkthroughs=None,
        contributes_task_definitions=None,
        contributes_terminal_profiles=None,
        capability_metadata=None,
    )
    mock_write.assert_called_once()


def test_execute_analysis_request_fails_closed_when_trigger_build_fails() -> None:
    """Trigger payload failures should abort analysis before sandbox automation starts."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            side_effect=ValueError("bad trigger"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ) as mock_run,
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="activation_report.json",
        )

    assert exc_info.value.error_code == "trigger_build_failed"
    assert progress_events[-1] == (
        "build_triggers",
        "failed",
        "Trigger payload build failed before sandbox automation started.",
        "trigger_build_failed",
    )
    mock_run.assert_not_called()


def test_execute_analysis_request_reports_reset_failure() -> None:
    """Reset failures should be reported on the reset step before bubbling up."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            side_effect=ExecutorError("reset failed", returncode=1, output="boom"),
        ),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
        )

    assert progress_events[-1] == (
        "reset_sandbox",
        "failed",
        "Sandbox reset failed before extension installation.",
        None,
    )


def test_execute_analysis_request_reports_automation_failure() -> None:
    """Automation failures should mark the monitoring step as failed."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["scenario"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            side_effect=ExecutorError("automation failed", returncode=1, output="boom"),
        ),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
        )

    assert progress_events[-1] == (
        "run_monitoring",
        "failed",
        "Sandbox automation failed before the report could be finalized.",
        None,
    )


def test_execute_analysis_request_reports_healthful_monitoring_summary(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "healthy",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 1,
            "failed_scenarios": ["coding_session"]
          },
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "completed"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": ["workspace_bootstrap"]}
          ],
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "layered_passes"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["coding_session"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
        )

    assert response.status == "success"
    assert any(
        step == "run_monitoring"
        and "trigger requested=true, loaded=true, applied=true" in message.lower()
        for step, _, message, _ in progress_events
    )
    assert any(
        step == "finalize_report"
        and "health=healthy" in message.lower()
        and "failed scenarios=1" in message.lower()
        for step, _, message, _ in progress_events
    )


@pytest.mark.parametrize("status", ["degraded", "inconclusive"])
def test_build_report_messages_include_extra_trigger_failures(
    status: str,
) -> None:
    monitoring_message, finalize_message = analysis_service._build_report_messages(
        "activation_report.json",
        payload={
            "automation_health": {
                "status": status,
                "trigger_requested": True,
                "trigger_loaded": True,
                "trigger_applied": False,
                "target_activation_count": 0,
                "failed_scenarios": ["coding_session"],
            },
            "summary": {
                "scenarios_run": ["coding_session"],
            },
            "extra_trigger_failures": ["uri_trigger", "command:Extension: Fail"],
        },
    )

    assert f"{status} health" in monitoring_message.lower()
    assert "extra trigger failures=2" in monitoring_message.lower()
    assert "failed scenarios=1" in finalize_message.lower()
    assert "extra trigger failures=2" in finalize_message.lower()


def test_execute_analysis_request_reports_degraded_monitoring_summary(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "degraded",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 1,
            "failed_scenarios": ["coding_session"],
            "extra_trigger_failures": ["uri_trigger", "command:Extension: Fail"],
            "extra_trigger_failure_count": 2
          },
          "extra_trigger_failures": [
            "uri_trigger",
            "command:Extension: Fail"
          ],
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "completed"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": ["workspace_bootstrap"]}
          ],
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "layered_passes"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["coding_session"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
        )

    assert response.status == "success"
    assert "extra trigger failures=2" in response.message.lower()
    assert any(
        step == "run_monitoring"
        and "degraded health" in message.lower()
        and "extra trigger failures=2" in message.lower()
        for step, _, message, _ in progress_events
    )
    assert any(
        step == "finalize_report"
        and "failed scenarios=1" in message.lower()
        and "extra trigger failures=2" in message.lower()
        for step, _, message, _ in progress_events
    )


def test_execute_analysis_request_fails_when_trigger_report_cannot_load(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["coding_session"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="missing_report.json",
        )

    assert exc_info.value.error_code == "trigger_load_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][1] == "failed"
    assert progress_events[-1][3] == "trigger_load_failed"


def test_execute_analysis_request_fails_when_trigger_plan_not_applied(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "selected_scenarios",
          "automation_health": {
            "status": "inconclusive",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": false,
            "target_activation_count": 0,
            "failed_scenarios": []
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["coding_session"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
        )

    assert exc_info.value.error_code == "trigger_apply_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][3] == "trigger_apply_failed"


def test_execute_analysis_request_fails_when_layered_evidence_is_missing(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "layered_passes",
          "automation_health": {
            "status": "degraded",
            "trigger_requested": true,
            "trigger_loaded": true,
            "trigger_applied": true,
            "target_activation_count": 0,
            "failed_scenarios": []
          },
          "stimulus_passes": [
            {"pass_id": "workspace_bootstrap", "status": "planned"}
          ],
          "event_attempts": [
            {"attempt_id": "official-onLanguage-python", "attempted_passes": []}
          ]
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="reset",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="install",
        ),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=("/results/triggers.json", ["coding_session"], "selected"),
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            return_value="automation",
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
        )

    assert exc_info.value.error_code == "trigger_apply_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][3] == "trigger_apply_failed"


def test_run_analysis_job_marks_failure_and_closes_session() -> None:
    """Background jobs should persist failure details when execution aborts."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=FileNotFoundError("missing report"),
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with("job-1", "missing report", error_code=None)
    session.close.assert_called_once_with()


def test_run_analysis_job_persists_trigger_error_code() -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    error = analysis_service.TriggerPlanError(
        "trigger_apply_failed",
        "Executor did not apply the trigger payload during sandbox automation.",
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=error,
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "Executor did not apply the trigger payload during sandbox automation.",
        error_code="trigger_apply_failed",
    )


def test_run_analysis_job_marks_completion_and_closes_session() -> None:
    """Background jobs should persist the final success payload."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    response = AnalyzeResponse(
        status="success",
        publisher=request.publisher,
        name=request.name,
        version=request.version,
        message="done",
        install_output="install-ok",
        automation_output="automation-ok",
        report_path="activation_report.json",
    )
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.complete_job"
        ) as mock_complete,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            return_value=response,
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_complete.assert_called_once_with("job-1", response)
    session.close.assert_called_once_with()


def test_run_analysis_job_marks_value_error_failure() -> None:
    """ValueError should fail background jobs instead of leaving them running."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=ValueError("bad trigger payload"),
        ),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "bad trigger payload",
        error_code=None,
    )
    session.close.assert_called_once_with()


def test_run_analysis_job_marks_type_error_failure_and_reraises() -> None:
    """Unexpected worker bugs should fail the job before the thread crashes."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=TypeError("planner wiring bug"),
        ),
        pytest.raises(TypeError, match="planner wiring bug"),
    ):
        analysis_service.run_analysis_job("job-1", request)

    mock_fail.assert_called_once_with(
        "job-1",
        "planner wiring bug",
        error_code=None,
    )
    session.close.assert_called_once_with()


def test_map_executor_error_for_install_branch() -> None:
    """Install-related executor failures should get a specific HTTP detail."""
    exc = analysis_service.ExecutorError(
        "Install failed",
        returncode=1,
        output="boom",
    )

    mapped = analysis_service.map_executor_error(exc)

    assert mapped.status_code == 502
    assert "install extension" in mapped.detail.lower()


def test_analyze_vsix_not_found_404(client: TestClient) -> None:
    """Missing .vsix file returns 404."""
    with patch(
        "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_analyze_install_failure_502(client: TestClient) -> None:
    """ExecutorError during install returns 502."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            side_effect=ExecutorError("Install failed", returncode=1, output="error"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "install extension" in response.json()["detail"].lower()


def test_analyze_automation_failure_502(client: TestClient) -> None:
    """ExecutorError during automation returns 502."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.analysis_service.reset_executor_sandbox_state",
            return_value="Sandbox reset.",
        ),
        patch(
            "workflows.marketplace.analysis_service.install_extension_in_executor",
            return_value="ok",
        ),
        patch(
            "workflows.marketplace.analysis_service.run_playwright_automation",
            side_effect=ExecutorError("Automation crashed", returncode=1, output="err"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "Automation crashed" in response.json()["detail"]


def test_analyze_trigger_plan_failure_502(client: TestClient) -> None:
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=analysis_service.TriggerPlanError(
                "trigger_apply_failed",
                "Executor did not apply the trigger payload during sandbox automation.",
            ),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "trigger payload" in response.json()["detail"].lower()


def test_analyze_start_returns_job_snapshot(client: TestClient) -> None:
    """Async analyze start returns a queued job payload."""
    job_snapshot = {
        "job_id": "job-123",
        "status": "queued",
        "publisher": ANALYZE_PAYLOAD["publisher"],
        "name": ANALYZE_PAYLOAD["name"],
        "version": ANALYZE_PAYLOAD["version"],
        "scenario": None,
        "current_step": None,
        "message": "Queued for sandbox analysis.",
        "steps": [
            {"name": "reset_sandbox", "status": "pending", "message": "Waiting"},
            {"name": "install_extension", "status": "pending", "message": "Queued"},
            {"name": "build_triggers", "status": "pending", "message": "Waiting"},
            {"name": "run_monitoring", "status": "pending", "message": "Waiting"},
            {"name": "finalize_report", "status": "pending", "message": "Waiting"},
        ],
        "report_path": "activation_report_ms-python.python-2025.0.0-job123.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": None,
        "error_code": None,
        "created_at": 1.0,
        "started_at": None,
        "finished_at": None,
        "updated_at": 1.0,
    }
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.job_service.reserve_job",
            return_value=job_snapshot,
        ),
        patch(
            "workflows.marketplace.router.job_service.get_job_snapshot",
            return_value=job_snapshot,
        ),
        patch("workflows.marketplace.router.threading.Thread") as mock_thread,
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["publisher"] == ANALYZE_PAYLOAD["publisher"]
    assert len(payload["steps"]) == 5
    assert payload["report_path"].startswith(
        "activation_report_ms-python.python-2025.0.0-"
    )
    mock_thread.return_value.start.assert_called_once()


def test_analyze_start_rejects_second_active_job(client: TestClient) -> None:
    """Single-sandbox mode should reject overlapping analysis jobs."""
    active_job = {"job_id": "running-job"}
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.job_service.reserve_job",
            side_effect=marketplace_router.job_service.ActiveAnalysisJobError(
                active_job
            ),
        ),
        patch("workflows.marketplace.router.threading.Thread") as mock_thread,
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 409
    assert "already in progress" in response.json()["detail"].lower()
    mock_thread.return_value.start.assert_not_called()


def test_analyze_start_missing_vsix_404(client: TestClient) -> None:
    """Async analyze start validates the VSIX before queueing a job."""
    with patch(
        "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
        return_value=_vsix_path_exists(False),
    ):
        response = client.post("/api/marketplace/analyze/start", json=ANALYZE_PAYLOAD)

    assert response.status_code == 404
    assert "VSIX file not found" in response.json()["detail"]


def test_get_analysis_job_status_404(client: TestClient) -> None:
    """Unknown analysis jobs return 404."""
    with patch(
        "workflows.marketplace.router.job_service.get_job_snapshot",
        side_effect=KeyError("missing-job"),
    ):
        response = client.get("/api/marketplace/analyze/missing-job")
    assert response.status_code == 404


def test_analyze_missing_publisher_422(client: TestClient) -> None:
    """Missing publisher field returns 422."""
    response = client.post(
        "/api/marketplace/analyze",
        json={"name": "python", "version": "2025.0.0"},
    )
    assert response.status_code == 422
