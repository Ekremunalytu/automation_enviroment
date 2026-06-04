"""Static decision-gate truth-table tests (ES-3b core, ADR 0016 §Decision 1).

Covers ``evaluate_static_gate`` across the severity x promoted-blocker matrix,
plus the ``_PROMOTED_HIGH_BLOCKERS`` frozenset invariant (every promoted id is
a real production static rule).
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticDetectionReport,
    StaticGateDecision,
)
from workflows.marketplace.static_analysis import (
    _PROMOTED_HIGH_BLOCKERS,
    evaluate_static_gate,
)

_PROMOTED_TYPOSQUAT = "extrace.s2.typosquat"


def _finding(
    *,
    rule_id: str,
    severity: Severity,
    confidence: Confidence = Confidence.MEDIUM,
    categories: tuple[str, ...] = ("attack.T1036",),
) -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id=rule_id,
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=list(categories),
        severity=severity,
        confidence=confidence,
        title="finding-title",
        description="finding-description",
    )


def _report(*findings: StaticDetectionFinding) -> StaticDetectionReport:
    return StaticDetectionReport(findings=list(findings))


def test_empty_report_allows() -> None:
    outcome = evaluate_static_gate(_report())
    assert outcome.decision is StaticGateDecision.ALLOW
    assert outcome.blocked_by == []
    assert outcome.warned_by == []
    assert outcome.allow_reason is not None


def test_critical_finding_blocks() -> None:
    outcome = evaluate_static_gate(
        _report(
            _finding(
                rule_id="extrace.a1.credential_read_then_network",
                severity=Severity.CRITICAL,
            )
        )
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == ["extrace.a1.credential_read_then_network"]
    assert outcome.allow_reason is None


def test_promoted_high_typosquat_blocks() -> None:
    outcome = evaluate_static_gate(
        _report(_finding(rule_id=_PROMOTED_TYPOSQUAT, severity=Severity.HIGH))
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == [_PROMOTED_TYPOSQUAT]


def test_non_promoted_high_only_warns() -> None:
    # A HIGH finding NOT in the promoted set warns, it does not block.
    outcome = evaluate_static_gate(
        _report(_finding(rule_id="extrace.a3.typosquat", severity=Severity.HIGH))
    )
    assert outcome.decision is StaticGateDecision.WARN
    assert outcome.warned_by == ["extrace.a3.typosquat"]
    assert outcome.blocked_by == []


@pytest.mark.parametrize("severity", [Severity.MEDIUM, Severity.LOW])
def test_medium_and_low_warn(severity: Severity) -> None:
    outcome = evaluate_static_gate(
        _report(_finding(rule_id="extrace.s1.activation_wildcard", severity=severity))
    )
    assert outcome.decision is StaticGateDecision.WARN
    assert outcome.warned_by == ["extrace.s1.activation_wildcard"]


def test_info_only_allows() -> None:
    # INFO is informational; it neither blocks nor warns on its own.
    outcome = evaluate_static_gate(
        _report(
            _finding(
                rule_id="extrace.s3.unusual_file_signature", severity=Severity.INFO
            )
        )
    )
    assert outcome.decision is StaticGateDecision.ALLOW
    assert outcome.warned_by == []


def test_block_precedence_over_warn() -> None:
    # A CRITICAL alongside MEDIUM findings still blocks; only the blocking
    # rule id lands in blocked_by, and warned_by stays empty on a BLOCK.
    outcome = evaluate_static_gate(
        _report(
            _finding(
                rule_id="extrace.s1.suspicious_capabilities", severity=Severity.MEDIUM
            ),
            _finding(
                rule_id="extrace.a1.credential_read_then_network",
                severity=Severity.CRITICAL,
            ),
        )
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == ["extrace.a1.credential_read_then_network"]
    assert outcome.warned_by == []


def test_promoted_typosquat_at_non_high_severity_does_not_block() -> None:
    # The promotion is gated on HIGH severity; the same rule id at MEDIUM warns.
    outcome = evaluate_static_gate(
        _report(_finding(rule_id=_PROMOTED_TYPOSQUAT, severity=Severity.MEDIUM))
    )
    assert outcome.decision is StaticGateDecision.WARN
    assert outcome.warned_by == [_PROMOTED_TYPOSQUAT]


def test_blocked_by_is_deduped_and_sorted() -> None:
    outcome = evaluate_static_gate(
        _report(
            _finding(rule_id="extrace.z.rule", severity=Severity.CRITICAL),
            _finding(rule_id="extrace.a.rule", severity=Severity.CRITICAL),
            _finding(rule_id="extrace.a.rule", severity=Severity.CRITICAL),
        )
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == ["extrace.a.rule", "extrace.z.rule"]


def test_warned_by_is_deduped_and_sorted() -> None:
    outcome = evaluate_static_gate(
        _report(
            _finding(
                rule_id="extrace.s3.embedded_native_binary", severity=Severity.MEDIUM
            ),
            _finding(rule_id="extrace.s1.generic_publisher", severity=Severity.LOW),
            _finding(rule_id="extrace.s1.generic_publisher", severity=Severity.LOW),
        )
    )
    assert outcome.decision is StaticGateDecision.WARN
    assert outcome.warned_by == [
        "extrace.s1.generic_publisher",
        "extrace.s3.embedded_native_binary",
    ]


def test_promoted_blockers_are_real_production_static_rules() -> None:
    """Every promoted blocker id must name a live production static rule.

    Guards against a typo'd / stale id silently disabling the sole HIGH
    block path. Importing the static registry here is intentional — the gate
    promotes by ``rule_id``, so the ids must stay in sync with the registry.
    """
    from static_runtime.rules.registry import get_production_rules

    production_ids = {rule.rule_id for rule in get_production_rules()}
    assert _PROMOTED_HIGH_BLOCKERS, "the promoted-blocker set must not be empty"
    assert production_ids >= _PROMOTED_HIGH_BLOCKERS


# ---------------------------------------------------------------------------
# Block-reason policy (ES-5 `static-typosquat-confidence-wording`)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "confidence", [Confidence.LOW, Confidence.MEDIUM, Confidence.HIGH]
)
def test_promoted_block_is_policy_driven_independent_of_confidence(
    confidence: Confidence,
) -> None:
    """The promoted-HIGH typosquat block is a POLICY decision, not a confidence one.

    ADR 0016 §Decision 1 promotes ``extrace.s2.typosquat`` to BLOCK by *rule id*
    at HIGH *severity*; the gate reads severity + rule_id and never the finding's
    ``confidence`` (the rule emits MEDIUM confidence by design, parity with the
    dynamic ``a3``). This pins the wording fix: "HIGH-severity promoted blocker",
    not "HIGH-confidence". A promoted HIGH finding blocks at ANY confidence and
    always names its rule id as the machine-readable cause.
    """
    assert _PROMOTED_TYPOSQUAT in _PROMOTED_HIGH_BLOCKERS
    outcome = evaluate_static_gate(
        _report(
            _finding(
                rule_id=_PROMOTED_TYPOSQUAT,
                severity=Severity.HIGH,
                confidence=confidence,
            )
        )
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == [_PROMOTED_TYPOSQUAT]


def test_critical_block_is_severity_driven_not_policy_gated() -> None:
    """A CRITICAL finding blocks on severity alone — promotion is not required.

    Distinguishes the two block reasons so a future refactor cannot collapse them:
    CRITICAL => severity-driven (any rule id); HIGH => only when the rule id is in
    ``_PROMOTED_HIGH_BLOCKERS``. Pairs with
    ``test_non_promoted_high_only_warns`` (a non-promoted HIGH warns, never
    blocks).
    """
    non_promoted = "extrace.s9.not_promoted"
    assert non_promoted not in _PROMOTED_HIGH_BLOCKERS
    outcome = evaluate_static_gate(
        _report(_finding(rule_id=non_promoted, severity=Severity.CRITICAL))
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == [non_promoted]


@pytest.mark.parametrize(
    "rule_id",
    [
        "extrace.s12.invisible_unicode_run",
        "extrace.s13.native_node_loader",
    ],
)
def test_glassworm_critical_static_rules_block(rule_id: str) -> None:
    """GlassWorm-strength static findings block by CRITICAL severity.

    UC2 invisible Unicode runs and the NL3 native-loader conjunction do not need
    promotion in ``_PROMOTED_HIGH_BLOCKERS``; the ADR 0016 gate blocks any
    CRITICAL finding before the dynamic sandbox.
    """
    assert rule_id not in _PROMOTED_HIGH_BLOCKERS
    outcome = evaluate_static_gate(
        _report(_finding(rule_id=rule_id, severity=Severity.CRITICAL))
    )
    assert outcome.decision is StaticGateDecision.BLOCK
    assert outcome.blocked_by == [rule_id]
