from __future__ import annotations

import pytest

import scripts.generate_ui_contracts as generator


def test_vsix_threshold_contracts_are_generated_targets() -> None:
    expected = {
        "ThresholdBoundsResponse",
        "ThresholdsResponse",
        "ThresholdsUpdateRequest",
        "VsixThresholdBreachDetail",
    }

    assert expected <= set(generator.TARGET_SCHEMAS)
    assert (
        generator.NAME_OVERRIDES["ThresholdBoundsResponse"] == "VsixThresholdBoundsDto"
    )
    assert generator.NAME_OVERRIDES["ThresholdsResponse"] == "VsixThresholdsResponseDto"
    assert (
        generator.NAME_OVERRIDES["ThresholdsUpdateRequest"]
        == "VsixThresholdsUpdateRequestDto"
    )
    assert (
        generator.NAME_OVERRIDES["VsixThresholdBreachDetail"]
        == "VsixThresholdBreachDetail"
    )


def test_vsix_threshold_contract_rendering_stays_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        generator,
        "TARGET_SCHEMAS",
        [
            "ThresholdBoundsResponse",
            "ThresholdsResponse",
            "ThresholdsUpdateRequest",
            "VsixThresholdBreachDetail",
        ],
    )
    schemas = {
        "ThresholdBoundsResponse": {
            "type": "object",
            "required": ["min_value", "max_value"],
            "properties": {
                "min_value": {"type": "integer"},
                "max_value": {"type": "integer"},
            },
        },
        "ThresholdsResponse": {
            "type": "object",
            "required": ["values", "defaults", "bounds", "keys"],
            "properties": {
                "values": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "defaults": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "bounds": {
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/components/schemas/ThresholdBoundsResponse"
                    },
                },
                "keys": {"type": "array", "items": {"type": "string"}},
            },
        },
        "ThresholdsUpdateRequest": {
            "type": "object",
            "properties": {
                "values": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "updated_by": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                },
            },
        },
        "VsixThresholdBreachDetail": {
            "type": "object",
            "required": [
                "error",
                "breach_kind",
                "threshold_name",
                "threshold_value",
                "observed_value",
                "message",
                "publisher",
                "name",
                "version",
            ],
            "properties": {
                "error": {"const": "vsix_threshold_breach", "type": "string"},
                "breach_kind": {
                    "enum": [
                        "entry_count",
                        "uncompressed_size",
                        "compression_ratio",
                    ],
                    "type": "string",
                },
                "threshold_name": {"type": "string"},
                "threshold_value": {"type": "integer"},
                "observed_value": {
                    "anyOf": [{"type": "integer"}, {"type": "number"}],
                },
                "message": {"type": "string"},
                "publisher": {"type": "string"},
                "name": {"type": "string"},
                "version": {"type": "string"},
            },
        },
    }

    rendered = generator._render_contracts(schemas)

    assert "export interface VsixThresholdBoundsDto" in rendered
    assert "bounds: Record<string, VsixThresholdBoundsDto>;" in rendered
    assert "export interface VsixThresholdBreachDetail" in rendered
    assert 'error: "vsix_threshold_breach";' in rendered
    assert (
        'breach_kind: "entry_count" | "uncompressed_size" | "compression_ratio";'
        in rendered
    )
    assert "observed_value: number;" in rendered
