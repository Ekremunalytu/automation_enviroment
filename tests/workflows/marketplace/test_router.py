"""
Tests for Marketplace Router
=============================

Tests for /api/marketplace/search and /api/marketplace/download endpoints.
All external calls (HTTP + DB writes) are mocked via unittest.mock.patch.
"""

import json
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


def test_download_threshold_breach_returns_structured_422(client: TestClient) -> None:
    """W12-* hardening: when ``download_and_extract_vsix`` raises
    ``VSIXUnpackError`` with structured breach metadata, the router maps
    it to HTTP 422 with a JSON detail object the UI popup can consume."""
    from workflows.marketplace.client import (
        VSIX_BREACH_ENTRY_COUNT,
        VSIXUnpackError,
    )

    err = VSIXUnpackError(
        "VSIX archive exceeds entry count limit (50000)",
        breach_kind=VSIX_BREACH_ENTRY_COUNT,
        threshold_name="vsix_max_file_count",
        threshold_value=50_000,
        observed_value=50_001,
    )

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2026.5.2026050801",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "vsix_threshold_breach"
    assert detail["breach_kind"] == VSIX_BREACH_ENTRY_COUNT
    assert detail["threshold_name"] == "vsix_max_file_count"
    assert detail["threshold_value"] == 50_000
    assert detail["observed_value"] == 50_001
    assert detail["publisher"] == "ms-python"
    assert detail["name"] == "python"
    assert detail["version"] == "2026.5.2026050801"


def test_download_threshold_breach_accepts_float_observed_value(
    client: TestClient,
) -> None:
    from workflows.marketplace.client import (
        VSIX_BREACH_COMPRESSION_RATIO,
        VSIXUnpackError,
    )

    err = VSIXUnpackError(
        "VSIX compression ratio 101.5:1 exceeds limit (100:1)",
        breach_kind=VSIX_BREACH_COMPRESSION_RATIO,
        threshold_name="vsix_max_compression_ratio",
        threshold_value=100,
        observed_value=101.5,
    )

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2026.5.2026050801",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["breach_kind"] == VSIX_BREACH_COMPRESSION_RATIO
    assert detail["observed_value"] == 101.5


def test_download_legacy_vsix_unpack_error_falls_back_to_string_detail(
    client: TestClient,
) -> None:
    """Older raise sites that do not pass ``breach_kind`` keep the
    backwards-compat HTTPException with a plain string detail (still 422,
    so the UI surfaces a generic threshold error rather than 500)."""
    from workflows.marketplace.client import VSIXUnpackError

    err = VSIXUnpackError("legacy unstructured failure")

    with patch(
        "workflows.marketplace.client.download_and_extract_vsix",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/download",
            json={
                "publisher": "ms-python",
                "name": "python",
                "version": "2025.0.0",
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "legacy unstructured failure"


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


def _resolve_exact_fixture(
    publisher: str,
    name: str,
    version: str,
) -> tuple[Path, Path]:
    extensions_dir = Path(marketplace_router.settings.project.EXTENSION_DIR)
    vsix_path = extensions_dir / f"{publisher}.{name}-{version}.vsix"
    extracted_dir = extensions_dir / f"{publisher}.{name}-{version}"
    if not vsix_path.exists():
        pytest.skip(f"{publisher}.{name} VSIX fixture is unavailable")
    if not extracted_dir.exists():
        pytest.skip(f"{publisher}.{name} extracted fixture directory is unavailable")
    return vsix_path, extracted_dir


def _make_trigger_plan(
    *,
    trigger_container_path: str | None = "/results/triggers.json",
    selected_scenarios: list[str] | None = None,
    skip_automation: bool = False,
    reason_code: str = "generated_trigger_plan",
    message: str = "Trigger plan ready.",
) -> trigger_service.TriggerPlan:
    return trigger_service.TriggerPlan(
        trigger_container_path=trigger_container_path,
        selected_scenarios=selected_scenarios or [],
        skip_automation=skip_automation,
        reason_code=reason_code,
        message=message,
    )


def _make_executor_control(
    *,
    reset_sandbox: object = "Sandbox reset.",
    install_extension: object = "Extension installed successfully.",
    run_automation: object = "Automation completed.",
) -> MagicMock:
    control = MagicMock(spec=analysis_service.ExecutorControl)
    control.reset_sandbox.side_effect = (
        reset_sandbox if isinstance(reset_sandbox, Exception) else None
    )
    control.install_extension.side_effect = (
        install_extension if isinstance(install_extension, Exception) else None
    )
    control.run_automation.side_effect = (
        run_automation if isinstance(run_automation, Exception) else None
    )

    if not isinstance(reset_sandbox, Exception):
        control.reset_sandbox.return_value = str(reset_sandbox)
    if not isinstance(install_extension, Exception):
        control.install_extension.return_value = str(install_extension)
    if not isinstance(run_automation, Exception):
        control.run_automation.return_value = str(run_automation)
    return control


def _scenario_zero_report_payload(target_extension_id: str) -> dict[str, object]:
    automation_health = {
        "status": "healthy",
        "reasons": [],
        "trigger_requested": False,
        "trigger_loaded": False,
        "trigger_applied": False,
        "extension_host_log_present": False,
        "extension_host_output_present": False,
        "target_stream_present": False,
        "target_activation_count": 0,
        "failed_scenarios": [],
        "extra_trigger_failures": [],
        "extra_trigger_failure_count": 0,
        "extension_host_log_found": False,
    }
    log_health = {
        "extension_host_log_found": False,
        "extension_host_output_present": False,
        "target_extension_log_entries": 0,
        "total_activation_entries": 0,
    }
    signal_summary = {
        "level": "benign",
        "score": 8,
        "note": "No executable surface was observed for the color-theme fixture.",
    }
    return {
        "report_version": 2,
        "target_extension_expected": target_extension_id,
        "target_extension_observed": False,
        "trigger_plan_requested": False,
        "trigger_plan_loaded": False,
        "trigger_plan_applied": False,
        "trigger_plan_path": "",
        "trigger_execution_mode": "skip_automation",
        "requested_scenarios": [],
        "failed_scenarios": [],
        "extra_trigger_failures": [],
        "verification_gap": 0,
        "heuristic_verification_gap": 0,
        "run_quality": "scenario_zero",
        "run_quality_reasons": [
            "No automation scenario was required for this non-executable fixture."
        ],
        "automation_health": automation_health,
        "log_health": log_health,
        "attribution_summary": {},
        "risk_signals": [],
        "risk_summary": {},
        "signal_summary": signal_summary,
        "summary": {
            "total_activated": 0,
            "unique_extensions": 0,
            "unique_event_extensions": 0,
            "running_extensions": 0,
            "monitoring_duration_s": 0.0,
            "monitoring_started_at": 0.0,
            "monitoring_ended_at": 0.0,
            "extension_ids": [],
            "scenarios_run": [],
            "failed_scenarios": [],
            "network_events": 0,
            "network_hosts": 0,
            "file_events": 0,
            "sensitive_file_events": 0,
            "target_file_events": 0,
            "target_network_events": 0,
            "attempted_capabilities": [],
            "verified_capabilities": [],
            "official_attempted_capabilities": [],
            "official_verified_capabilities": [],
            "heuristic_attempted_capabilities": [],
            "heuristic_verified_capabilities": [],
            "ui_blocker_count": 0,
            "target_extension_expected": target_extension_id,
            "target_extension_observed": False,
            "official_event_coverage": {},
            "heuristic_workflow_coverage": {},
            "trigger_execution_mode": "skip_automation",
            "trigger_plan_applied": False,
            "verification_gap": 0,
            "heuristic_verification_gap": 0,
            "run_quality": "scenario_zero",
            "automation_health": automation_health,
            "log_health": log_health,
            "attribution_summary": {},
            "risk_summary": {},
            "signal_summary": signal_summary,
        },
        "attempted_capabilities": [],
        "verified_capabilities": [],
        "official_attempted_capabilities": [],
        "official_verified_capabilities": [],
        "heuristic_attempted_capabilities": [],
        "heuristic_verified_capabilities": [],
        "network_capture_error": "",
        "file_capture_error": "",
        "file_capture_diagnostics": {},
        "activated": [],
        "running_extensions": [],
        "scenario_traces": [],
        "stimulus_passes": [],
        "prerequisite_results": [],
        "event_attempts": [],
        "evidence_events": [],
        "evidence_links": [],
        "network_events": [],
        "network_summary": {},
        "file_events": [],
        "file_summary": {},
        "coverage_summary": {},
        "coverage_matrix": [],
        "coverage_tracks": {},
        "official_event_coverage": {},
        "heuristic_workflow_coverage": {},
        "extension_host_output_lines": 0,
        "extension_host_output": "",
        "log_streams": {
            "automation": [],
            "target_extension_host": [],
            "other_extension_host": [],
        },
        "log_file": "",
    }


def test_analyze_success(client: TestClient) -> None:
    """Successful analyze returns 200 with install and automation output."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            return_value=AnalyzeResponse(
                status="success",
                publisher="ms-python",
                name="python",
                version="2025.0.0",
                message="Analysis completed.",
                install_output="Extension installed successfully.",
                automation_output="Automation completed.",
                report_path="activation_report_ms-python.python-2025.0.0-fixture.json",
            ),
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

    plan = trigger_service.build_trigger_payload(db=MagicMock(), request=request)

    assert plan.trigger_container_path is None
    assert plan.selected_scenarios == []
    assert plan.skip_automation is False
    assert plan.reason_code == "explicit_scenario"
    assert "skipped" in plan.message.lower()


def test_build_trigger_payload_without_activation_events_preserves_fallback_planning() -> (
    None
):
    """Missing activation metadata should still compile a fallback trigger plan."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    payload = SimpleNamespace(
        selected_scenarios=["coding_session"],
        official_event_coverage={"declared": 0},
        stimulus_passes=[],
    )

    with (
        patch(
            "workflows.marketplace.trigger_service.get_extension_activation_events",
            return_value=[],
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_contributes_all",
            return_value=None,
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_capabilities",
            return_value=None,
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
        plan = trigger_service.build_trigger_payload(db=MagicMock(), request=request)

    assert plan.trigger_container_path == "/results/triggers.json"
    assert plan.selected_scenarios == ["coding_session"]
    assert plan.skip_automation is False
    assert plan.reason_code == "generated_trigger_plan"
    mock_select.assert_called_once()
    mock_write.assert_called_once()


def test_build_trigger_payload_returns_scenario_zero_for_theme_only_fixture() -> None:
    """Theme-only fixtures should still skip executor automation."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    contributes = SimpleNamespace(
        themes=[
            {
                "label": "Fixture Theme",
                "uiTheme": "vs-dark",
                "path": "./themes/fixture.json",
            }
        ]
    )
    payload = SimpleNamespace(
        selected_scenarios=["coding_session"],
        official_event_coverage={"declared": 0},
        stimulus_passes=[],
    )

    with (
        patch(
            "workflows.marketplace.trigger_service.get_extension_activation_events",
            return_value=[],
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_contributes_all",
            return_value=contributes,
        ),
        patch(
            "workflows.marketplace.trigger_service.get_extension_capabilities",
            return_value=None,
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
        plan = trigger_service.build_trigger_payload(db=MagicMock(), request=request)

    assert plan.trigger_container_path is None
    assert plan.selected_scenarios == []
    assert plan.skip_automation is True
    assert plan.reason_code == "non_executable_fixture"
    assert "scenario-zero" in plan.message.lower()
    mock_select.assert_called_once()
    mock_write.assert_not_called()


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
        plan = trigger_service.build_trigger_payload(db=MagicMock(), request=request)

    assert plan.trigger_container_path == "/results/triggers.json"
    assert plan.selected_scenarios == ["command_palette"]
    assert plan.skip_automation is False
    assert plan.reason_code == "generated_trigger_plan"
    assert "trigger requested for ms-python.python" in plan.message.lower()
    assert "/results/triggers.json" in plan.message
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
    executor_control = _make_executor_control()

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            side_effect=ValueError("bad trigger"),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="activation_report.json",
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_build_failed"
    assert progress_events[-1] == (
        "build_triggers",
        "failed",
        "Trigger payload build failed before sandbox automation started.",
        "trigger_build_failed",
    )
    executor_control.run_automation.assert_not_called()


def test_execute_analysis_request_reports_reset_failure() -> None:
    """Reset failures should be reported on the reset step before bubbling up."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control(
        reset_sandbox=ExecutorError("reset failed", returncode=1, output="boom")
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            executor_control=executor_control,
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
    executor_control = _make_executor_control(
        run_automation=ExecutorError("automation failed", returncode=1, output="boom")
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["scenario"],
                message="selected",
            ),
        ),
        pytest.raises(ExecutorError),
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            executor_control=executor_control,
        )

    assert progress_events[-1] == (
        "run_monitoring",
        "failed",
        (
            "Sandbox automation failed before the report could be finalized: "
            "automation failed"
        ),
        None,
    )


def test_execute_analysis_request_reports_healthful_monitoring_summary(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
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
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
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


def test_execute_analysis_request_rejects_legacy_trigger_plan_tuple(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    executor_control = _make_executor_control()
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
            "failed_scenarios": []
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
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=(
                "/results/triggers.json",
                ["coding_session"],
                "legacy trigger payload",
            ),
        ),
    ):
        with pytest.raises(
            TypeError, match="build_trigger_payload must return TriggerPlan"
        ):
            analysis_service.execute_analysis_request(
                request,
                db=MagicMock(),
                report_name=report_name,
                executor_control=executor_control,
            )


def test_execute_analysis_request_falls_back_to_selected_scenario_when_legacy_trigger_file_is_missing(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    report_name = "activation_report.json"
    (tmp_path / report_name).write_text(
        """
        {
          "trigger_execution_mode": "single_scenario",
          "automation_health": {
            "status": "inconclusive",
            "trigger_requested": true,
            "trigger_loaded": false,
            "trigger_applied": false,
            "target_activation_count": 0,
            "failed_scenarios": []
          },
          "summary": {
            "scenarios_run": ["coding_session"],
            "trigger_execution_mode": "single_scenario"
          }
        }
        """,
        encoding="utf-8",
    )

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                trigger_container_path="/results/missing-trigger-payload.json",
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert response.status == "success"
    assert (
        executor_control.run_automation.call_args.kwargs["scenario"] == "coding_session"
    )
    assert (
        executor_control.run_automation.call_args.kwargs["trigger_container_path"]
        == "/results/missing-trigger-payload.json"
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
    executor_control = _make_executor_control()
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
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
    ):
        response = analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
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
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")

    with (
        patch("workflows.marketplace.analysis_service.ensure_vsix_exists"),
        patch(
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name="missing_report.json",
            executor_control=executor_control,
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
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")
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
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
        )

    assert exc_info.value.error_code == "trigger_apply_failed"
    assert progress_events[-1][0] == "run_monitoring"
    assert progress_events[-1][3] == "trigger_apply_failed"


def test_execute_analysis_request_fails_when_layered_evidence_is_missing(
    tmp_path: Path,
) -> None:
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    progress_events: list[tuple[str, str, str, str | None]] = []
    executor_control = _make_executor_control()
    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    (tmp_path / "triggers.json").write_text("{}", encoding="utf-8")
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
            "workflows.marketplace.analysis_service.build_trigger_payload",
            return_value=_make_trigger_plan(
                selected_scenarios=["coding_session"],
                message="selected",
            ),
        ),
        pytest.raises(analysis_service.TriggerPlanError) as exc_info,
    ):
        analysis_service.execute_analysis_request(
            request,
            db=MagicMock(),
            progress_callback=lambda step, status, message, error_code=None, progress=None: (
                progress_events.append((step, status, message, error_code))
            ),
            report_name=report_name,
            executor_control=executor_control,
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


def test_run_analysis_job_swallows_cancellation_without_calling_fail_job() -> None:
    """AnalysisCancelledError must short-circuit silently — the job row was already
    marked cancelled by the /cancel endpoint, so a second fail_job would clobber it."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c1", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.job_service.complete_job"
        ) as mock_complete,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=analysis_service.AnalysisCancelledError("cancelled"),
        ),
    ):
        analysis_service.run_analysis_job("job-c1", request)

    mock_fail.assert_not_called()
    mock_complete.assert_not_called()
    session.close.assert_called_once_with()


def test_run_analysis_job_skips_fail_job_when_cancelled_during_executor_error() -> None:
    """If the user cancels mid-run, the executor often surfaces an ExecutorError
    when the sandbox reset interrupts it. fail_job must NOT overwrite the
    'cancelled' status set by the /cancel endpoint."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c2", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.is_job_cancelled",
            return_value=True,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.fail_job"
        ) as mock_fail,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=ExecutorError("sandbox reset interrupted run"),
        ),
    ):
        analysis_service.run_analysis_job("job-c2", request)

    mock_fail.assert_not_called()
    session.close.assert_called_once_with()


def test_run_analysis_job_progress_update_swallows_keyerror_when_job_vanishes() -> None:
    """The background heartbeat keeps emitting after the row could be deleted in
    rare edge cases (e.g. interactive tests). progress_update must not crash the
    automation thread when update_job_step raises KeyError."""
    request = AnalyzeRequest(**ANALYZE_PAYLOAD)
    session = MagicMock()
    captured_callback: dict[str, object] = {}

    def fake_execute(*_args, **kwargs):
        captured_callback["cb"] = kwargs["progress_callback"]
        # Fire a progress update from the executor side and then short-circuit.
        kwargs["progress_callback"](
            "run_monitoring",
            "running",
            "Scenario 1/2",
            None,
            {"completed": 1, "total": 2},
        )
        raise analysis_service.AnalysisCancelledError("cancelled")

    with (
        patch(
            "workflows.marketplace.analysis_service._open_job_session",
            return_value=session,
        ),
        patch(
            "workflows.marketplace.analysis_service.job_service.get_job_snapshot",
            return_value={"job_id": "job-c3", "report_path": "saved-report.json"},
        ),
        patch("workflows.marketplace.analysis_service.job_service.update_job"),
        patch(
            "workflows.marketplace.analysis_service.job_service.update_job_step",
            side_effect=KeyError("job-c3"),
        ) as mock_update_step,
        patch(
            "workflows.marketplace.analysis_service.execute_analysis_request",
            side_effect=fake_execute,
        ),
    ):
        # Should NOT raise — KeyError is swallowed inside progress_update.
        analysis_service.run_analysis_job("job-c3", request)

    assert mock_update_step.call_count >= 1
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
    assert "error_id=" in mapped.detail


def test_map_executor_error_redacts_internal_paths_and_env(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raw exception text must not surface in HTTP detail; logger keeps it."""
    leaky = analysis_service.ExecutorError(
        "Internal /etc/secrets/db.pem read failed; HOME=/home/operator/.config",
        returncode=1,
        output="POSTGRES_PASSWORD=hunter2",
    )

    with caplog.at_level("WARNING", logger="workflows.marketplace.analysis_service"):
        mapped = analysis_service.map_executor_error(leaky)

    detail = mapped.detail
    assert mapped.status_code == 502
    assert "/etc/" not in detail
    assert "/home/" not in detail
    assert "POSTGRES_PASSWORD" not in detail
    assert "hunter2" not in detail
    assert detail.startswith("Automation failed in sandbox.")
    assert "error_id=" in detail

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "executor_error" in logged
    assert "/etc/secrets/db.pem" in logged


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
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=ExecutorError("Install failed", returncode=1, output="error"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    assert "install extension" in response.json()["detail"].lower()


def test_analyze_automation_failure_502(client: TestClient) -> None:
    """ExecutorError during automation returns 502 with redacted detail."""
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=ExecutorError("Automation crashed", returncode=1, output="err"),
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail.startswith("Automation failed in sandbox.")
    assert "error_id=" in detail
    assert "Automation crashed" not in detail


@pytest.mark.integration
def test_theme_fixture_analysis_uses_scenario_zero_flow(
    db_client: TestClient,
    tmp_path: Path,
) -> None:
    publisher = "extrace"
    name = "fixture-theme"
    version = "0.0.1"
    target_extension_id = f"{publisher}.{name}"
    _vsix_path, extracted_dir = _resolve_exact_fixture(publisher, name, version)
    assert extracted_dir.exists()

    report_payload = _scenario_zero_report_payload(target_extension_id)
    original_output_dir = marketplace_router.settings.project.OUTPUT_DIR

    class ScenarioZeroExecutorControl:
        def reset_sandbox(self, reload_window: bool = True) -> str:
            assert reload_window is True
            return "Sandbox reset."

        def install_extension(
            self, install_publisher: str, install_name: str, install_version: str
        ) -> str:
            assert (install_publisher, install_name, install_version) == (
                publisher,
                name,
                version,
            )
            return "Extension installed successfully."

        def run_automation(
            self,
            *,
            report_path: str,
            scenario: str | None = None,
            trigger_container_path: str | None = None,
            skip_automation: bool = False,
            reload_before_run: bool = False,
            target_extension_id: str | None = None,
        ) -> str:
            assert scenario is None
            assert trigger_container_path is None
            assert skip_automation is True
            assert reload_before_run is True
            assert target_extension_id == f"{publisher}.{name}"
            resolved_report_path = tmp_path / Path(report_path).name
            resolved_report_path.write_text(
                json.dumps(report_payload, indent=2),
                encoding="utf-8",
            )
            return "Automation skipped for scenario-zero analysis."

    marketplace_router.settings.project.OUTPUT_DIR = str(tmp_path)
    try:
        with patch(
            "workflows.marketplace.analysis_service.default_executor_control",
            ScenarioZeroExecutorControl(),
        ):
            download_response = db_client.post(
                "/api/marketplace/download",
                json={
                    "publisher": publisher,
                    "name": name,
                    "version": version,
                },
            )
            assert download_response.status_code == 200

            response = db_client.post(
                "/api/marketplace/analyze",
                json={
                    "publisher": publisher,
                    "name": name,
                    "version": version,
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["report_path"].endswith(".json")
        assert "health=healthy" in payload["message"].lower()

        report_response = db_client.get(f"/api/activations/{payload['report_path']}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["target_extension_expected"] == target_extension_id
        assert report["trigger_execution_mode"] == "skip_automation"
        assert report["summary"]["scenarios_run"] == []
        assert report["summary"]["failed_scenarios"] == []
        assert report["scenario_traces"] == []
        assert report["stimulus_passes"] == []
        assert report["event_attempts"] == []
        assert report["run_quality"] == "scenario_zero"
        assert report["trigger_plan_requested"] is False
        assert report["trigger_plan_loaded"] is False
        assert report["trigger_plan_applied"] is False
        assert report["automation_health"]["status"] == "healthy"
        assert report["automation_health"]["target_activation_count"] == 0
    finally:
        marketplace_router.settings.project.OUTPUT_DIR = original_output_dir


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


def test_cancel_analysis_job_returns_cancelled_snapshot(client: TestClient) -> None:
    cancelled_snapshot = {
        "job_id": "job-456",
        "status": "cancelled",
        "publisher": "ms-python",
        "name": "python",
        "version": "2025.0.0",
        "scenario": None,
        "current_step": "run_monitoring",
        "message": "Cancelled by user.",
        "steps": [
            {"name": "reset_sandbox", "status": "completed", "message": "ok"},
            {"name": "install_extension", "status": "completed", "message": "ok"},
            {"name": "build_triggers", "status": "completed", "message": "ok"},
            {
                "name": "run_monitoring",
                "status": "cancelled",
                "message": "Cancelled by user.",
            },
            {"name": "finalize_report", "status": "skipped", "message": "Skipped"},
        ],
        "report_path": "activation_report_ms-python.python-2025.0.0-job456.json",
        "install_output": None,
        "automation_output": None,
        "error_detail": "Cancelled by user.",
        "error_code": "cancelled_by_user",
        "created_at": 1.0,
        "started_at": 2.0,
        "finished_at": 3.0,
        "updated_at": 3.0,
    }
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        return_value=cancelled_snapshot,
    ) as mock_cancel:
        response = client.post("/api/marketplace/analyze/job-456/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["error_code"] == "cancelled_by_user"
    assert body["steps"][3]["status"] == "cancelled"
    mock_cancel.assert_called_once()


@pytest.mark.parametrize("terminal_status", ["completed", "failed", "cancelled"])
def test_cancel_analysis_job_terminal_returns_409(
    client: TestClient, terminal_status: str
) -> None:
    """A cancel request that races against any terminal-state transition
    surfaces 409 with the offending status preserved in the detail. Mirrors
    the CRUD-level cancel-after-finish race coverage; closes the router-side
    half of POST_POC_BACKLOG `[FOLLOWUP simulation-progress-cancel]`
    cancel-after-finish race gap."""
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        side_effect=marketplace_router.JobNotCancellableError(
            "job-789", terminal_status
        ),
    ):
        response = client.post("/api/marketplace/analyze/job-789/cancel")

    assert response.status_code == 409
    detail = response.json()["detail"].lower()
    assert "terminal status" in detail
    assert terminal_status in detail


def test_cancel_analysis_job_unknown_returns_404(client: TestClient) -> None:
    with patch(
        "workflows.marketplace.router.job_service.cancel_job",
        side_effect=KeyError("job-missing"),
    ):
        response = client.post("/api/marketplace/analyze/job-missing/cancel")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


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
