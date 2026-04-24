"""Risk signal and activation-layer signal summary policy helpers."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import importlib
import ipaddress
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .health import is_background_activation
    from .signal_facts import (
        indexed_target_activations,
        indexed_target_file_events,
        indexed_target_network_events,
        indexed_ui_blockers,
    )
except ImportError:  # pragma: no cover - top-level executor import mode
    from health import is_background_activation
    from signal_facts import (
        indexed_target_activations,
        indexed_target_file_events,
        indexed_target_network_events,
        indexed_ui_blockers,
    )


_PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_quantize_confidence = importlib.import_module(
    "packages.analysis_contracts.detection.enums"
).quantize_confidence


def _confidence_tier(value: float) -> str:
    return str(_quantize_confidence(value))


def _make_signal(risk_signal_type: Any, *, confidence: float, **fields: Any) -> Any:
    return risk_signal_type(
        confidence=confidence,
        confidence_tier=_confidence_tier(confidence),
        **fields,
    )


def build_risk_signals(report: Any, risk_signal_type: Any) -> list[Any]:
    signals: list[Any] = []
    target_activations = indexed_target_activations(report)
    background_activation_ids = [
        event_id
        for event_id, activation in target_activations
        if is_background_activation(getattr(activation, "activation_event", ""))
    ]
    strong_target_files = [
        (event_id, event)
        for event_id, event in indexed_target_file_events(report)
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]
    strong_target_networks = [
        (event_id, event)
        for event_id, event in indexed_target_network_events(report)
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]
    sensitive_target_files = [
        (event_id, event)
        for event_id, event in strong_target_files
        if getattr(event, "sensitive", False)
    ]
    correlated_groups: dict[str, list[tuple[str, float, float, str]]] = defaultdict(
        list
    )
    for index, file_event in enumerate(getattr(report, "file_events", []), start=1):
        if getattr(file_event, "attribution_status", "") in {
            "near_target_activation",
            "competing_candidate",
        } and getattr(file_event, "sensitive", False):
            event_id = f"file-{index:04d}"
            rel_time_s = getattr(file_event, "rel_time_s", None)
            if isinstance(rel_time_s, int | float):
                correlated_groups[
                    str(getattr(file_event, "related_activation_event", "")).strip()
                ].append(
                    (
                        event_id,
                        float(rel_time_s),
                        getattr(file_event, "attribution_confidence", 0.0),
                        "file",
                    )
                )
    for index, network_event in enumerate(
        getattr(report, "network_events", []), start=1
    ):
        if getattr(network_event, "attribution_status", "") in {
            "near_target_activation",
            "competing_candidate",
        } and _is_correlative_network_candidate(network_event):
            event_id = f"network-{index:04d}"
            rel_time_s = getattr(network_event, "rel_time_s", None)
            if isinstance(rel_time_s, int | float):
                correlated_groups[
                    str(getattr(network_event, "related_activation_event", "")).strip()
                ].append(
                    (
                        event_id,
                        float(rel_time_s),
                        getattr(network_event, "attribution_confidence", 0.0),
                        "network",
                    )
                )

    if background_activation_ids and sensitive_target_files:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="background_sensitive_file_access",
                category="background_sensitive_file_access",
                severity="high",
                confidence=max(
                    0.82,
                    max(
                        getattr(event, "attribution_confidence", 0.0)
                        for _, event in sensitive_target_files
                    ),
                ),
                evidence_event_ids=background_activation_ids
                + [event_id for event_id, _ in sensitive_target_files],
                summary=(
                    "The target extension touched sensitive files after a startup or "
                    "background activation."
                ),
            )
        )
    if background_activation_ids and strong_target_networks:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="background_outbound_network",
                category="background_outbound_network",
                severity="high",
                confidence=max(
                    0.78,
                    max(
                        getattr(event, "attribution_confidence", 0.0)
                        for _, event in strong_target_networks
                    ),
                ),
                evidence_event_ids=background_activation_ids
                + [event_id for event_id, _ in strong_target_networks],
                summary=(
                    "Outbound network activity followed a startup or background target "
                    "activation."
                ),
            )
        )
    if sensitive_target_files:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="credential_or_secret_access",
                category="credential_or_secret_access",
                severity="high",
                confidence=max(
                    0.84,
                    max(
                        getattr(event, "attribution_confidence", 0.0)
                        for _, event in sensitive_target_files
                    ),
                ),
                evidence_event_ids=[event_id for event_id, _ in sensitive_target_files],
                summary=(
                    "The target extension accessed credential or secret-bearing paths "
                    "with strong attribution."
                ),
            )
        )
    if len({getattr(event, "path", "") for _, event in sensitive_target_files}) >= 2:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="multiple_sensitive_artifacts",
                category="multiple_sensitive_artifacts",
                severity="high",
                confidence=0.9,
                evidence_event_ids=[event_id for event_id, _ in sensitive_target_files],
                summary=(
                    "Multiple distinct sensitive artifacts were touched by the target "
                    "extension."
                ),
            )
        )
    if sensitive_target_files and strong_target_networks:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="sensitive_file_and_network_combo",
                category="sensitive_file_and_network_combo",
                severity="critical",
                confidence=0.94,
                evidence_event_ids=[event_id for event_id, _ in sensitive_target_files]
                + [event_id for event_id, _ in strong_target_networks],
                summary=(
                    "Sensitive local access and outbound network activity were both "
                    "strongly attributed to the target extension."
                ),
            )
        )
    qualifying_correlated_events: list[tuple[str, float, str]] = []
    for activation_event, grouped_events in correlated_groups.items():
        if not activation_event:
            continue
        if len(grouped_events) < 2:
            continue
        ordered_group = sorted(grouped_events, key=lambda item: item[1])
        if ordered_group[-1][1] - ordered_group[0][1] > 5.0:
            continue
        kinds = {item[3] for item in ordered_group}
        if "file" not in kinds or "network" not in kinds:
            continue
        qualifying_correlated_events = [
            (event_id, confidence, activation_event)
            for event_id, _rel_time_s, confidence, _kind in ordered_group
        ]
        break

    if qualifying_correlated_events:
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="correlative_suspicious_activity",
                category="correlative_suspicious_activity",
                severity="medium",
                confidence=max(
                    0.35,
                    max(
                        confidence for _, confidence, _ in qualifying_correlated_events
                    ),
                ),
                evidence_event_ids=[
                    event_id for event_id, _, _ in qualifying_correlated_events
                ],
                summary=(
                    "Suspicious telemetry was observed near target activations, but the "
                    "evidence remains correlative."
                ),
            )
        )
    if getattr(report, "ui_blocker_entries", []):
        signals.append(
            _make_signal(
                risk_signal_type,
                signal_id="ui_blocker_verification_gap",
                category="ui_blocker_verification_gap",
                severity="medium",
                confidence=1.0,
                evidence_event_ids=[
                    event_id for event_id, _ in indexed_ui_blockers(report)
                ],
                summary=(
                    "UI blockers interrupted the run and reduced verification certainty."
                ),
            )
        )
    return signals


def _is_correlative_network_candidate(network_event: Any) -> bool:
    host = str(getattr(network_event, "host", "")).strip()
    if _is_loopback_or_infra_peer(host):
        return False
    source_ip = str(getattr(network_event, "source_ip", "")).strip()
    destination_ip = str(getattr(network_event, "destination_ip", "")).strip()
    return not (
        _is_loopback_or_infra_peer(source_ip)
        or _is_loopback_or_infra_peer(destination_ip)
    )


def _is_loopback_or_infra_peer(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    if normalized.startswith("localhost"):
        return True
    peer = normalized
    if peer.startswith("[") and "]" in peer:
        peer = peer[1 : peer.index("]")]
    elif peer.count(":") == 1 and peer.rsplit(":", maxsplit=1)[1].isdigit():
        peer = peer.rsplit(":", maxsplit=1)[0]
    try:
        return ipaddress.ip_address(peer).is_loopback
    except ValueError:
        return False


def build_risk_summary(signals: list[Any]) -> dict[str, Any]:
    severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for signal in signals:
        severity = getattr(signal, "severity", "")
        if severity in severities:
            severities[severity] += 1
    return {
        "total_signals": len(signals),
        "critical": severities["critical"],
        "high": severities["high"],
        "medium": severities["medium"],
        "low": severities["low"],
        "categories": [getattr(signal, "category", "") for signal in signals],
    }


def build_signal_summary(
    report: Any,
    *,
    automation_health: dict[str, Any],
    run_quality: tuple[str, list[str]],
) -> dict[str, Any]:
    target_id = getattr(report, "target_extension_id", "")
    if not target_id:
        return {
            "level": "needs_review",
            "score": 25,
            "reasons": [
                "Target extension context was missing, so ownership could not be evaluated."
            ],
            "note": "Target extension context was missing, so the run can only be reviewed manually.",
        }

    quality_level, quality_reasons = run_quality
    health_status = automation_health.get("status", "inconclusive")
    if (
        not getattr(report, "target_extension_observed", False)
        or health_status == "inconclusive"
    ):
        inconclusive_reasons = [
            "The target extension was not observed, so the run remains inconclusive."
        ]
        inconclusive_reasons.extend(quality_reasons)
        return {
            "level": "needs_review",
            "score": 30,
            "reasons": inconclusive_reasons[:5],
            "note": inconclusive_reasons[0],
        }

    target_activations = [
        entry
        for entry in getattr(report, "activated", [])
        if getattr(entry, "extension_id", "") == target_id
    ]
    startup_target = any(
        is_background_activation(getattr(entry, "activation_event", ""))
        for entry in target_activations
    )
    strong_target_files = [
        event
        for event in getattr(report, "target_file_events", [])
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]
    strong_target_networks = [
        event
        for event in getattr(report, "target_network_events", [])
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]
    sensitive_target_files = [
        event for event in strong_target_files if getattr(event, "sensitive", False)
    ]
    correlated_sensitive_files = [
        event
        for event in getattr(report, "file_events", [])
        if getattr(event, "sensitive", False)
        and getattr(event, "attribution_status", "")
        in {"near_target_activation", "competing_candidate"}
    ]
    reasons: list[str] = []
    score = 8

    if startup_target and sensitive_target_files:
        score += 28
        reasons.append(
            "The target extension activated in a background/startup path and then touched sensitive files."
        )
    if startup_target and strong_target_networks:
        score += 20
        reasons.append(
            "The target extension emitted network activity after a background or eager activation."
        )
    if any(
        getattr(event, "scenario_name", "")
        in {"settings_modification", "project_exploration"}
        and getattr(event, "sensitive", False)
        for event in sensitive_target_files
    ):
        score += 18
        reasons.append(
            "Sensitive file access happened while scanning workspace/settings-oriented scenarios."
        )
    if any(
        getattr(event, "scenario_name", "") in {"terminal_usage", "debug_session"}
        and getattr(event, "sensitive", False)
        for event in sensitive_target_files
    ):
        score += 18
        reasons.append(
            "Credential or secret paths were accessed during terminal/debug-oriented hooks."
        )
    if len({getattr(event, "path", "") for event in sensitive_target_files}) >= 2:
        score += 22
        reasons.append(
            "Multiple distinct sensitive artifacts were touched with strong target attribution."
        )
    if sensitive_target_files and strong_target_networks:
        score += 22
        reasons.append(
            "Sensitive local access and outbound network activity both belong to the target extension."
        )
    if correlated_sensitive_files and not sensitive_target_files:
        score += 14
        reasons.append(
            "Sensitive file activity exists near target activations, but attribution is only correlative."
        )
    if getattr(report, "ui_blocker_entries", []):
        score += 5
        reasons.append(
            "UI blockers were detected, which reduced verification certainty for parts of the run."
        )
    if getattr(report, "trigger_plan_requested", False) and not getattr(
        report, "trigger_plan_applied", False
    ):
        score += 8
        reasons.append(
            "The trigger plan was not applied inside the executor, which reduced run reliability."
        )
    if quality_level == "low":
        score += 6
        reasons.append(
            "Run quality was low, so suspicious telemetry is weighted conservatively but not dismissed."
        )

    score = max(8, min(96, score))
    strong_attribution = bool(sensitive_target_files or strong_target_networks)
    if (
        strong_attribution
        and score >= 70
        and (
            strong_target_networks
            or len({getattr(event, "path", "") for event in sensitive_target_files})
            >= 2
        )
    ):
        level = "likely_malicious"
    elif score >= 48:
        level = "suspicious"
    elif reasons or quality_level in {"low", "medium"}:
        level = "needs_review"
    else:
        level = "benign"

    if not strong_attribution and level == "likely_malicious":
        level = "suspicious"
    if not strong_attribution and level == "suspicious" and score < 60:
        level = "needs_review"
    if quality_level in {"low", "medium"} and level == "benign":
        level = "needs_review"
    if health_status != "healthy" and level == "benign":
        level = "needs_review"

    note = (
        reasons[0]
        if reasons
        else (
            "The run did not produce strongly attributed high-risk behavior from the target extension."
        )
    )
    return {
        "level": level,
        "score": score,
        "reasons": reasons[:5],
        "note": note,
    }
