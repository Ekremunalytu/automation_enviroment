import pytest
from pydantic import ValidationError

from appcore.contracts.schema_defs.analysis_jobs import (
    AnalysisJobStepProgress,
    AnalysisJobStepRecord,
    AnalysisJobStepUpdate,
)
from appcore.contracts.schema_defs.executor_settings import (
    ExecutorPreferencesResponse,
    ExecutorPreferencesUpdateRequest,
)
from appcore.contracts.schema_defs.marketplace import AnalyzeJobStepProgress
from appcore.contracts.schema_defs.security_settings import (
    ThresholdBoundsResponse,
    ThresholdsResponse,
    ThresholdsUpdateRequest,
)
from appcore.contracts.schemas import (
    ExtensionContributesSchema,
    ExtensionSchema,
)


def test_extension_schema_valid():
    data = {
        "name": "valid-ext",
        "publisher": "valid-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.name == "valid-ext"


def test_extension_schema_missing_field():
    data = {
        "name": "invalid-ext",
        # Missing publisher, version, engines
    }
    with pytest.raises(ValidationError) as exc:
        ExtensionSchema(**data)

    errors = exc.value.errors()
    missing_fields = [e["loc"][0] for e in errors]
    assert "publisher" in missing_fields
    assert "version" in missing_fields


def test_extension_schema_with_dependencies():
    """Test ExtensionSchema with dependencies and devDependencies fields."""
    data = {
        "name": "deps-ext",
        "publisher": "deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "dependencies": {"axios": "^1.0.0", "lodash": "^4.17.0"},
        "devDependencies": {"typescript": "^5.0.0", "@types/node": "^20.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.dependencies == {"axios": "^1.0.0", "lodash": "^4.17.0"}
    assert schema.devDependencies == {"typescript": "^5.0.0", "@types/node": "^20.0.0"}


def test_extension_schema_with_null_dependencies():
    """Test ExtensionSchema with null/missing dependencies fields."""
    data = {
        "name": "no-deps-ext",
        "publisher": "no-deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.dependencies is None
    assert schema.devDependencies is None


def test_extension_schema_with_extension_pack():
    """Test ExtensionSchema with extensionPack field."""
    data = {
        "name": "pack-ext",
        "publisher": "pack-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionPack": ["ms-python.python", "ms-python.vscode-pylance"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack == ["ms-python.python", "ms-python.vscode-pylance"]


def test_extension_schema_with_extension_dependencies():
    """Test ExtensionSchema with extensionDependencies field."""
    data = {
        "name": "deps-ext",
        "publisher": "deps-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionDependencies": ["ms-vscode.cpptools", "vscjava.vscode-java-pack"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionDependencies == [
        "ms-vscode.cpptools",
        "vscjava.vscode-java-pack",
    ]


def test_extension_schema_with_extension_kind():
    """Test ExtensionSchema with extensionKind field."""
    data = {
        "name": "kind-ext",
        "publisher": "kind-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionKind": ["ui", "workspace"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionKind == ["ui", "workspace"]


def test_extension_schema_with_all_extension_fields():
    """Test ExtensionSchema with all new extension fields populated."""
    data = {
        "name": "full-ext",
        "publisher": "full-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
        "extensionPack": ["bundle.ext1", "bundle.ext2"],
        "extensionDependencies": ["required.ext"],
        "extensionKind": ["workspace"],
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack == ["bundle.ext1", "bundle.ext2"]
    assert schema.extensionDependencies == ["required.ext"]
    assert schema.extensionKind == ["workspace"]


def test_extension_schema_with_null_extension_fields():
    """Test ExtensionSchema with null/missing extension fields."""
    data = {
        "name": "null-ext",
        "publisher": "null-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.0.0"},
    }
    schema = ExtensionSchema(**data)
    assert schema.extensionPack is None
    assert schema.extensionDependencies is None
    assert schema.extensionKind is None


def test_extension_contributes_schema_defaults():
    """Test ExtensionContributesSchema default values."""
    schema = ExtensionContributesSchema()
    assert schema.configuration is None
    assert schema.keybindings == []
    assert schema.menus == []
    assert schema.authentication == []
    assert schema.terminal == []
    assert schema.commands == []


def test_extension_contributes_schema_with_children():
    """Test ExtensionContributesSchema with child contribution data."""
    data = {
        "configuration": {"title": "Config"},
        "keybindings": [
            {"key": "ctrl+k", "command": "ext.hello", "when": "editorTextFocus"}
        ],
        "commands": [{"command_id": "ext.hello", "title": "Hello"}],
        "menus": [{"menu_location": "editor/context", "command": "ext.hello"}],
        "authentication": [{"auth_id": "github", "label": "GitHub"}],
        "terminal": [{"profile_id": "ext.term", "title": "Ext Terminal"}],
    }
    schema = ExtensionContributesSchema(**data)

    assert schema.configuration == {"title": "Config"}
    assert schema.keybindings[0].command == "ext.hello"
    assert schema.commands[0].command_id == "ext.hello"
    assert schema.menus[0].menu_location == "editor/context"
    assert schema.authentication[0].auth_id == "github"
    assert schema.terminal[0].profile_id == "ext.term"


def test_extension_contributes_schema_configuration_as_list():
    """`contributes.configuration` may be an array of config objects.

    VS Code permits both a single configuration object and a list of them
    (e.g. GitHub Copilot ships a list). Regression: the list form must not
    raise a pydantic dict_type error.
    """
    data = {
        "configuration": [
            {"title": "GitHub Copilot", "properties": {"copilot.enable": {}}},
            {"title": "Advanced", "properties": {"copilot.advanced": {}}},
        ],
    }
    schema = ExtensionContributesSchema(**data)

    assert isinstance(schema.configuration, list)
    assert schema.configuration[0]["title"] == "GitHub Copilot"


# -- Analysis-job step progress contract --------------------------------------


def test_analysis_job_step_progress_accepts_zero_and_positive_counts() -> None:
    progress = AnalysisJobStepProgress(completed=0, total=5)
    assert progress.completed == 0
    assert progress.total == 5


def test_analysis_job_step_progress_rejects_negative_completed() -> None:
    with pytest.raises(ValidationError):
        AnalysisJobStepProgress(completed=-1, total=5)


def test_analysis_job_step_progress_rejects_negative_total() -> None:
    with pytest.raises(ValidationError):
        AnalysisJobStepProgress(completed=0, total=-1)


def test_analysis_job_step_progress_forbids_unknown_fields() -> None:
    """``extra='forbid'`` is the load-bearing guard against silently dropping
    a fat-fingered key like ``done``/``count`` that won't reach the UI."""
    with pytest.raises(ValidationError):
        AnalysisJobStepProgress(completed=1, total=2, done=1)  # type: ignore[call-arg]


def test_analysis_job_step_record_accepts_progress_field() -> None:
    record = AnalysisJobStepRecord(
        name="run_monitoring",
        status="running",
        message="Scenario 1/5",
        progress=AnalysisJobStepProgress(completed=1, total=5),
    )
    assert record.progress is not None
    assert record.progress.completed == 1


def test_analysis_job_step_record_progress_defaults_to_none() -> None:
    record = AnalysisJobStepRecord(
        name="reset_sandbox",
        status="completed",
        message="ok",
    )
    assert record.progress is None


def test_analysis_job_step_update_accepts_cancelled_status() -> None:
    update = AnalysisJobStepUpdate(
        step_name="run_monitoring",
        status="cancelled",
        message="Cancelled by user.",
        error_code="cancelled_by_user",
    )
    assert update.status == "cancelled"


# -- Marketplace API DTO progress contract ------------------------------------


def test_analyze_job_step_progress_dto_rejects_negative_values() -> None:
    """The wire-facing DTO mirrors the storage schema's ge=0 constraint so the
    UI never sees a negative numerator/denominator from a misbehaving worker."""
    with pytest.raises(ValidationError):
        AnalyzeJobStepProgress(completed=-1, total=2)
    with pytest.raises(ValidationError):
        AnalyzeJobStepProgress(completed=0, total=-1)


def test_analyze_job_step_progress_dto_accepts_zero_total() -> None:
    """A zero total is legal at the schema layer; UI clamps progress when
    total is 0 to avoid divide-by-zero (covered separately in adapters)."""
    progress = AnalyzeJobStepProgress(completed=0, total=0)
    assert progress.completed == 0
    assert progress.total == 0


def test_thresholds_response_round_trips_with_typed_bounds() -> None:
    payload = {
        "values": {"vsix_max_file_count": 75_000},
        "defaults": {"vsix_max_file_count": 50_000},
        "bounds": {"vsix_max_file_count": {"min_value": 1, "max_value": 200_000}},
        "keys": ["vsix_max_file_count"],
    }
    parsed = ThresholdsResponse.model_validate(payload)
    assert parsed.bounds["vsix_max_file_count"] == ThresholdBoundsResponse(
        min_value=1, max_value=200_000
    )
    assert parsed.model_dump(mode="json") == payload


def test_thresholds_response_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        ThresholdsResponse.model_validate({"values": {}, "defaults": {}, "bounds": {}})


def test_thresholds_update_request_defaults_values_to_empty_dict() -> None:
    req = ThresholdsUpdateRequest()
    assert req.values == {}
    assert req.updated_by is None


def test_thresholds_update_request_rejects_overlong_updated_by() -> None:
    with pytest.raises(ValidationError):
        ThresholdsUpdateRequest(updated_by="x" * 129)


def test_executor_preferences_contract_requires_a_strict_boolean() -> None:
    response = ExecutorPreferencesResponse(dynamic_analysis_enabled=False)
    assert response.model_dump(mode="json") == {"dynamic_analysis_enabled": False}

    request = ExecutorPreferencesUpdateRequest(dynamic_analysis_enabled=True)
    assert request.dynamic_analysis_enabled is True

    with pytest.raises(ValidationError):
        ExecutorPreferencesUpdateRequest(dynamic_analysis_enabled=1)
