"""W10-1 contract tests: ``ActivationReport.schema_version`` evolution gate.

Proactive replacement for the reactive ``_migrate_legacy_verdict`` pattern
(W7 fallout). Every ``ActivationReport`` now carries ``schema_version``;
legacy ingest (missing or stale) emits ``DeprecationWarning`` and is
rejected when ``model_validate(..., context={"strict_schema": True})``.
"""

from __future__ import annotations

import json
import warnings
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.analysis_contracts import (
    ACTIVATION_REPORT_SCHEMA_VERSION,
    ActivationReport,
)


_FIXTURE = (
    Path(__file__).parent / "fixtures" / "activation_reports" / "ms_python_python.json"
)


def _load_baseline() -> dict[str, object]:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_current_schema_version_round_trip_is_silent() -> None:
    payload = _load_baseline()
    payload["schema_version"] = ACTIVATION_REPORT_SCHEMA_VERSION

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        parsed = ActivationReport.model_validate(payload)

    assert parsed.schema_version == ACTIVATION_REPORT_SCHEMA_VERSION
    dumped = parsed.model_dump(mode="json")
    assert dumped["schema_version"] == ACTIVATION_REPORT_SCHEMA_VERSION
    reparsed = ActivationReport.model_validate(dumped)
    assert reparsed == parsed


def test_missing_schema_version_emits_deprecation_warning_and_defaults() -> None:
    payload = _load_baseline()
    payload.pop("schema_version", None)

    with pytest.warns(DeprecationWarning, match="without schema_version"):
        parsed = ActivationReport.model_validate(payload)

    assert parsed.schema_version == ACTIVATION_REPORT_SCHEMA_VERSION


def test_missing_schema_version_rejected_under_strict_schema() -> None:
    payload = _load_baseline()
    payload.pop("schema_version", None)

    with pytest.raises(ValidationError, match="schema_version missing"):
        ActivationReport.model_validate(payload, context={"strict_schema": True})


def test_stale_schema_version_emits_deprecation_warning() -> None:
    payload = _load_baseline()
    payload["schema_version"] = "0.5"

    with pytest.warns(DeprecationWarning, match="stale schema_version"):
        ActivationReport.model_validate(payload)


def test_stale_schema_version_rejected_under_strict_schema() -> None:
    payload = _load_baseline()
    payload["schema_version"] = "0.5"

    with pytest.raises(ValidationError, match="does not match current"):
        ActivationReport.model_validate(payload, context={"strict_schema": True})


def test_legacy_verdict_ingest_still_accepted_with_schema_version_warning() -> None:
    """Composability: missing schema_version + legacy verdict field both
    transformed in the same model_validate call."""
    payload = _load_baseline()
    payload.pop("schema_version", None)
    legacy = deepcopy(payload)
    legacy["verdict"] = legacy.pop("signal_summary")
    assert "verdict" in legacy
    assert "signal_summary" not in legacy

    with pytest.warns(DeprecationWarning, match="without schema_version"):
        parsed = ActivationReport.model_validate(legacy)

    dumped = parsed.model_dump(mode="json")
    assert "verdict" not in dumped
    assert "signal_summary" in dumped
    assert dumped["schema_version"] == ACTIVATION_REPORT_SCHEMA_VERSION
