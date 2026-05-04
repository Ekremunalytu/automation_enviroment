"""Tests for workflows.marketplace.triggers — smart activation trigger selection."""

import json
from pathlib import Path

import pytest

from packages.analysis_contracts import TriggerPayload
from packages.marketplace_identity import MarketplaceIdentityError
from workflows.marketplace.triggers import (
    CAPABILITY_TAXONOMY,
    glob_to_bait_filename,
    build_static_coverage_audit,
    select_scenarios,
    write_trigger_file,
)

# ---------------------------------------------------------------------------
# select_scenarios
# ---------------------------------------------------------------------------


class TestSelectScenarios:
    """Tests for the select_scenarios function."""

    def test_wildcard_selects_all_scenarios(self) -> None:
        events = [{"event_type": "*", "event_value": None}]
        payload = select_scenarios(events)
        assert "coding_session" in payload.selected_scenarios
        assert "project_exploration" in payload.selected_scenarios
        assert "diagnostics_check" in payload.selected_scenarios
        assert len(payload.selected_scenarios) == 5
        assert payload.official_selected_scenarios == []
        assert payload.official_attempted_capabilities == []
        assert payload.heuristic_attempted_capabilities

    def test_on_startup_finished_selects_all(self) -> None:
        events = [{"event_type": "onStartupFinished", "event_value": None}]
        payload = select_scenarios(events)
        assert len(payload.selected_scenarios) == 5
        assert payload.official_attempted_capabilities == []

    def test_on_language_selects_coding_and_exploration(self) -> None:
        events = [{"event_type": "onLanguage", "event_value": "python"}]
        payload = select_scenarios(events)
        assert "coding_session" in payload.selected_scenarios
        assert "project_exploration" in payload.selected_scenarios
        assert payload.official_selected_scenarios == [
            "coding_session",
            "project_exploration",
        ]
        assert "commands" in payload.official_attempted_capabilities
        assert payload.selection_reasons["coding_session"] == [
            "activation onLanguage:python"
        ]

    def test_on_debug_selects_debug_session(self) -> None:
        events = [{"event_type": "onDebug", "event_value": "python"}]
        payload = select_scenarios(events)
        assert "debug_session" in payload.selected_scenarios
        attempt = next(
            item
            for item in payload.event_attempts
            if item.activation_event == "onDebug:python"
        )
        assert attempt.executor_action == "extra:debug_lifecycle"

    def test_on_view_scm_selects_git_workflow(self) -> None:
        events = [{"event_type": "onView", "event_value": "scm"}]
        payload = select_scenarios(events)
        assert "git_workflow" in payload.selected_scenarios
        assert payload.official_selected_scenarios == []
        assert "scm" in payload.heuristic_attempted_capabilities
        assert payload.coverage_tracks["heuristic"]["matrix"]

    def test_on_view_extensions_selects_browsing(self) -> None:
        events = [{"event_type": "onView", "event_value": "extensions"}]
        payload = select_scenarios(events)
        assert "extension_browsing" in payload.selected_scenarios
        assert payload.official_attempted_capabilities == []

    def test_on_view_unknown_falls_back_to_exploration(self) -> None:
        events = [{"event_type": "onView", "event_value": "customPanel"}]
        payload = select_scenarios(events)
        assert "project_exploration" in payload.selected_scenarios
        assert payload.official_attempted_capabilities == []

    def test_on_notebook_adds_notebook_session_and_file(self) -> None:
        events = [{"event_type": "onNotebook", "event_value": "jupyter-notebook"}]
        payload = select_scenarios(events)
        assert "notebook_session" in payload.selected_scenarios
        assert "notebooks/analysis.ipynb" in payload.extra_notebook_files

    def test_on_task_type_sets_trigger(self) -> None:
        events = [{"event_type": "onTaskType", "event_value": "npm"}]
        payload = select_scenarios(events)
        assert payload.run_task_trigger is True
        assert "terminal_usage" in payload.selected_scenarios

    def test_on_walkthrough_sets_trigger(self) -> None:
        events = [{"event_type": "onWalkthrough", "event_value": "myWalkthrough"}]
        payload = select_scenarios(events)
        assert payload.run_walkthrough_trigger is True

    def test_on_uri_sets_trigger_with_publisher(self) -> None:
        events = [{"event_type": "onUri", "event_value": None}]
        payload = select_scenarios(events, publisher_name="pub.ext")
        assert payload.uri_trigger == "vscode://pub.ext/activate"
        assert payload.target_extension_id == "pub.ext"

    def test_on_uri_without_publisher_no_trigger(self) -> None:
        events = [{"event_type": "onUri", "event_value": None}]
        payload = select_scenarios(events)
        assert payload.uri_trigger is None

    def test_on_configuration_selects_settings(self) -> None:
        events = [{"event_type": "onConfiguration", "event_value": "myext.setting"}]
        payload = select_scenarios(events)
        assert "settings_modification" in payload.selected_scenarios
        assert payload.official_attempted_capabilities == []
        assert "settings" in payload.heuristic_attempted_capabilities

    def test_on_authentication_request_selects_authentication_probe(self) -> None:
        events = [{"event_type": "onAuthenticationRequest", "event_value": "github"}]
        payload = select_scenarios(events)
        assert "authentication_probe" in payload.selected_scenarios
        assert payload.auth_provider_ids == ["github"]

    def test_on_webview_panel_selects_webview_probe(self) -> None:
        events = [{"event_type": "onWebviewPanel", "event_value": "sampleView"}]
        payload = select_scenarios(events)
        assert "webview_probe" in payload.selected_scenarios
        assert payload.webview_view_ids == ["sampleView"]
        attempt = next(
            item
            for item in payload.event_attempts
            if item.activation_event == "onWebviewPanel:sampleView"
        )
        assert attempt.executor_action == "harness:run_current_stimulus"

    def test_workspace_contains_selects_exploration(self) -> None:
        events = [{"event_type": "workspaceContains", "event_value": "**/.gitignore"}]
        payload = select_scenarios(events)
        assert "project_exploration" in payload.selected_scenarios

    def test_empty_events_falls_back_to_coding_session(self) -> None:
        payload = select_scenarios([])
        assert payload.selected_scenarios == ["coding_session"]
        assert payload.coverage_summary.covered == 0
        assert payload.official_attempted_capabilities == []
        assert payload.heuristic_attempted_capabilities == [
            "commands",
            "languages_editor",
            "window_ui",
            "workspace_fs",
        ]

    def test_unknown_event_type_falls_back(self) -> None:
        events = [{"event_type": "onSomethingNew", "event_value": None}]
        payload = select_scenarios(events)
        assert payload.selected_scenarios == ["coding_session"]

    def test_multiple_events_combine_scenarios(self) -> None:
        events = [
            {"event_type": "onLanguage", "event_value": "python"},
            {"event_type": "onDebug", "event_value": "python"},
            {"event_type": "onView", "event_value": "scm"},
        ]
        payload = select_scenarios(events)
        assert "coding_session" in payload.selected_scenarios
        assert "debug_session" in payload.selected_scenarios
        assert "git_workflow" in payload.selected_scenarios
        assert "project_exploration" in payload.selected_scenarios

    def test_scenarios_are_sorted(self) -> None:
        events = [
            {"event_type": "onDebug", "event_value": "python"},
            {"event_type": "onLanguage", "event_value": "python"},
        ]
        payload = select_scenarios(events)
        assert payload.selected_scenarios == [
            "coding_session",
            "debug_session",
            "project_exploration",
        ]

    def test_payload_contains_coverage_matrix_for_all_capabilities(self) -> None:
        payload = select_scenarios(
            [{"event_type": "onLanguage", "event_value": "python"}]
        )

        assert len(payload.coverage_matrix) == len(CAPABILITY_TAXONOMY)
        commands = next(
            item for item in payload.coverage_matrix if item["capability"] == "commands"
        )
        missing = next(
            item for item in payload.coverage_matrix if item["capability"] == "chat"
        )
        assert commands["status"] == "covered"
        assert commands["track"] == "official"
        assert commands["source"] == "official_activation_track"
        assert commands["support_status"] == "covered"
        assert missing["status"] == "missing"

    def test_authentication_and_webview_are_reported_as_covered_when_selected(
        self,
    ) -> None:
        payload = select_scenarios(
            [
                {"event_type": "onAuthenticationRequest", "event_value": "github"},
                {"event_type": "onWebviewPanel", "event_value": "sampleView"},
            ]
        )

        authentication = next(
            item
            for item in payload.coverage_matrix
            if item["capability"] == "authentication"
        )
        webview = next(
            item for item in payload.coverage_matrix if item["capability"] == "webview"
        )
        assert authentication["status"] == "covered"
        assert webview["status"] == "covered"

    def test_unsupported_official_capabilities_stay_out_of_attempted_list(self) -> None:
        payload = select_scenarios(
            [
                {"event_type": "onLanguageModelTool", "event_value": "tool.sample"},
            ],
            capability_metadata={"untrusted_supported": False},
        )

        assert "chat" not in payload.official_attempted_capabilities
        missing = next(
            item for item in payload.coverage_matrix if item["capability"] == "chat"
        )
        assert missing["support_status"] == "missing"
        assert missing["status"] == "missing"

    def test_builtin_views_only_contribute_to_heuristic_track(self) -> None:
        payload = select_scenarios([{"event_type": "onView", "event_value": "search"}])

        assert payload.official_attempted_capabilities == []
        assert "search_views" in payload.heuristic_attempted_capabilities
        assert payload.coverage_tracks["official"]["selected_scenarios"] == []
        assert payload.coverage_tracks["heuristic"]["selected_scenarios"] == [
            "search_workflow"
        ]

    def test_contributed_webview_view_can_land_in_official_track(self) -> None:
        payload = select_scenarios(
            [{"event_type": "onView", "event_value": "webview.sample"}],
            contributes_views={"explorer": [{"id": "webview.sample"}]},
        )

        assert payload.official_selected_scenarios == ["webview_probe"]
        assert "webview" in payload.official_attempted_capabilities
        assert payload.heuristic_attempted_capabilities == []
        assert payload.view_targets["webview.sample"] == {
            "container_id": "explorer",
            "view_type": "",
        }

    def test_static_coverage_audit_exposes_missing_capabilities(self) -> None:
        audit = build_static_coverage_audit()

        assert audit["summary"]["missing"] >= 1
        assert "chat" in audit["summary"]["missing_capabilities"]
        assert any(
            entry["capability"] == "commands" and entry["status"] == "covered"
            for entry in audit["matrix"]
        )

    def test_custom_editors_creates_bait_files(self) -> None:
        events = [{"event_type": "onCustomEditor", "event_value": "myEditor"}]
        custom_editors = [
            {
                "viewType": "myEditor",
                "selector": [{"filenamePattern": "*.myext"}],
            }
        ]
        payload = select_scenarios(events, contributes_custom_editors=custom_editors)
        assert "bait.myext" in payload.extra_custom_editor_files

    def test_custom_editors_brace_expansion(self) -> None:
        custom_editors = [
            {
                "viewType": "imgViewer",
                "selector": [{"filenamePattern": "*.{png,jpg,gif}"}],
            }
        ]
        payload = select_scenarios([], contributes_custom_editors=custom_editors)
        assert "bait.png" in payload.extra_custom_editor_files

    def test_contributes_commands_populates_extra_commands(self) -> None:
        events = [{"event_type": "onCommand", "event_value": "myext.sayHello"}]
        commands = [
            {"title": "Say Hello", "command_id": "myext.sayHello"},
            {"title": "Run Analysis", "command_id": "myext.runAnalysis"},
        ]
        payload = select_scenarios(events, contributes_commands=commands)
        assert "Say Hello" in payload.extra_commands
        assert "Run Analysis" in payload.extra_commands
        assert len(payload.extra_commands) == 2
        assert payload.command_targets == {
            "myext.sayHello": "Say Hello",
            "myext.runAnalysis": "Run Analysis",
        }

    def test_contributes_commands_are_capped(self) -> None:
        commands = [
            {"title": f"Command {index}", "command_id": f"ext.command{index}"}
            for index in range(8)
        ]
        payload = select_scenarios([], contributes_commands=commands)
        assert len(payload.extra_commands) == 6
        assert payload.extra_commands[0] == "Command 0"
        assert payload.extra_commands[-1] == "Command 5"

    def test_no_contributes_commands_leaves_empty(self) -> None:
        events = [{"event_type": "onLanguage", "event_value": "python"}]
        payload = select_scenarios(events)
        assert payload.extra_commands == []


# ---------------------------------------------------------------------------
# write_trigger_file
# ---------------------------------------------------------------------------


class TestWriteTriggerFile:
    """Tests for write_trigger_file."""

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        payload = TriggerPayload(
            selected_scenarios=["coding_session", "debug_session"],
            uri_trigger="vscode://pub.ext/activate",
            run_task_trigger=True,
        )
        container_path = write_trigger_file(
            "pub", "ext", "1.0.0", payload, output_dir=str(tmp_path)
        )

        assert container_path == "/results/triggers_pub.ext-1.0.0.json"

        host_file = tmp_path / "triggers_pub.ext-1.0.0.json"
        assert host_file.exists()

        data = json.loads(host_file.read_text())
        validated = TriggerPayload.model_validate(data)

        assert data["selected_scenarios"] == ["coding_session", "debug_session"]
        assert data["uri_trigger"] == "vscode://pub.ext/activate"
        assert data["run_task_trigger"] is True
        assert data["run_walkthrough_trigger"] is False
        assert "coverage_summary" in data
        assert "coverage_matrix" in data
        assert validated.selected_scenarios == ["coding_session", "debug_session"]
        assert validated.uri_trigger == "vscode://pub.ext/activate"

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "output"
        payload = TriggerPayload(selected_scenarios=["coding_session"])
        write_trigger_file("p", "n", "1.0.0", payload, output_dir=str(output_dir))
        assert (output_dir / "triggers_p.n-1.0.0.json").exists()

    def test_rejects_adversarial_identity_before_writing(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        payload = TriggerPayload(selected_scenarios=["coding_session"])

        with pytest.raises(MarketplaceIdentityError):
            write_trigger_file(
                "../etc",
                "ext",
                "1.0.0",
                payload,
                output_dir=str(output_dir),
            )

        assert not output_dir.exists()


# ---------------------------------------------------------------------------
# glob_to_bait_filename
# ---------------------------------------------------------------------------


class TestGlobToBaitFilename:
    """Tests for the internal glob-to-filename converter."""

    def test_simple_extension(self) -> None:
        assert glob_to_bait_filename("*.csv") == "bait.csv"

    def test_brace_expansion(self) -> None:
        assert glob_to_bait_filename("*.{png,jpg}") == "bait.png"

    def test_directory_prefix(self) -> None:
        assert glob_to_bait_filename("**/*.csv") == "bait.csv"

    def test_concrete_filename(self) -> None:
        assert glob_to_bait_filename("config.yaml") == "config.yaml"

    def test_unsupported_glob_returns_none(self) -> None:
        assert glob_to_bait_filename("file?.txt") is None
