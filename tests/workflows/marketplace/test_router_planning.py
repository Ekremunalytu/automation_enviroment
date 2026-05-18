"""Tests for analyze-flow trigger-payload planning + happy-path analyze endpoint.

Split from tests/workflows/marketplace/test_router.py during W16-6 to reduce single-file size.
Covers test_analyze_success + build_trigger_payload helper tests.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from appcore.contracts.schemas import AnalyzeRequest, AnalyzeResponse
from workflows.marketplace import trigger_service


# ---------------------------------------------------------------------------
# Fixtures
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


# ---------------------------------------------------------------------------
# Analyze Tests — happy path + trigger-plan helpers
# ---------------------------------------------------------------------------


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

