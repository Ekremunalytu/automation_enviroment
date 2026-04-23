"""Headless A1 demo / W7 acceptance smoke.

Runs the package-local detection engine against the T1 A1
credential-read canary and asserts the PoC acceptance contract.

Usage:
    python scripts/demo_acceptance.py

Exit codes:
    0 -- all assertions passed; demo is green.
    1 -- one or more assertions failed (see stderr).

The script depends only on the framework-agnostic ``packages.*``
namespace; no FastAPI, no database, no Docker required.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from packages.analysis_contracts import (
    ActivationReport,
    ExtensionIdentity,
    detection_report_invariant_issues,
)
from packages.analysis_engine import run_detection

CANARY_DIR = REPO_ROOT / "extensions" / "malicious" / "t1-a1-credential-read-canary"
EXPECTED_RULE_ID = "extrace.a1.credential_read_then_network"
ACCEPTABLE_VERDICTS = {"malicious", "suspicious"}


def _load_canary() -> tuple[ActivationReport, dict]:
    fixture_path = CANARY_DIR / "activation_report.json"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Canary fixture missing at {fixture_path}. "
            "Check .gitignore allow-list for extensions/malicious/."
        )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return ActivationReport.model_validate(payload), payload


def _canary_identity() -> ExtensionIdentity:
    return ExtensionIdentity(
        publisher="extrace",
        name="t1-a1-credential-read-canary",
        version="0.0.1",
    )


def _fail(message: str) -> None:
    print(f"  [FAIL] {message}", file=sys.stderr)


def _ok(message: str) -> None:
    print(f"  [PASS] {message}")


def main() -> int:
    print(f"Loading canary: {CANARY_DIR.relative_to(REPO_ROOT)}")
    activation_report, activation_payload = _load_canary()

    detection_report = run_detection(
        activation_report,
        activation_report_ref="demo/t1-a1-credential-read-canary",
        analyzed_extension=_canary_identity(),
    )
    detection_payload = detection_report.model_dump(mode="json")

    print()
    print(f"Verdict: {detection_report.verdict.value}")
    print(f"Rationale: {detection_report.verdict_rationale}")
    print(f"Findings: {len(detection_report.findings)}")
    for finding in detection_report.findings:
        print(
            f"  - rule={finding.rule_id} severity={finding.severity.value} "
            f"confidence={finding.confidence.value}"
        )
        for evidence in finding.evidence:
            ref = evidence.model_dump(mode="json")
            print(
                f"      evidence event_id={ref.get('event_id')} type={ref.get('type')}"
            )

    print()
    print("Acceptance contract:")
    failures = 0

    # 1. Verdict is elevated above clean.
    verdict_value = detection_report.verdict.value
    if verdict_value in ACCEPTABLE_VERDICTS:
        _ok(f"verdict in {sorted(ACCEPTABLE_VERDICTS)} (got {verdict_value})")
    else:
        _fail(f"verdict expected in {sorted(ACCEPTABLE_VERDICTS)}, got {verdict_value}")
        failures += 1

    # 2. Exactly one finding fires the A1 rule.
    a1_findings = [
        f for f in detection_report.findings if f.rule_id == EXPECTED_RULE_ID
    ]
    if len(a1_findings) == 1:
        _ok(f"single finding fired from {EXPECTED_RULE_ID}")
    else:
        _fail(
            f"expected exactly one finding from {EXPECTED_RULE_ID}, got "
            f"{len(a1_findings)}"
        )
        failures += 1

    if a1_findings:
        finding = a1_findings[0]
        # 3. Severity critical + confidence high (matches §10.7 bar).
        if finding.severity.value == "critical" and finding.confidence.value == "high":
            _ok("finding severity=critical, confidence=high")
        else:
            _fail(
                "expected severity=critical, confidence=high; "
                f"got severity={finding.severity.value}, "
                f"confidence={finding.confidence.value}"
            )
            failures += 1

        # 4. Evidence refs carry both the file read and the network POST.
        evidence_types = {ref.type for ref in finding.evidence}
        if "filesystem_read" in evidence_types and "network_request" in evidence_types:
            _ok("evidence carries both filesystem_read and network_request refs")
        else:
            _fail(
                "expected evidence types to include filesystem_read + "
                f"network_request; got {sorted(evidence_types)}"
            )
            failures += 1

    # 5. Cross-layer link invariant holds.
    invariant_issues = detection_report_invariant_issues(
        detection_payload, activation_payload
    )
    if not invariant_issues:
        _ok("detection_report_invariant_issues == []")
    else:
        _fail(f"invariant issues: {invariant_issues}")
        failures += 1

    # 6. Runner reports no rule errors; A1 record status == fired.
    error_records = [
        record
        for record in detection_report.rules_executed
        if record.status.value == "error"
    ]
    if error_records:
        _fail(f"rule execution errors: {[r.rule_id for r in error_records]}")
        failures += 1
    else:
        _ok("no rule execution errors")

    a1_record = next(
        (
            record
            for record in detection_report.rules_executed
            if record.rule_id == EXPECTED_RULE_ID
        ),
        None,
    )
    if a1_record is None:
        _fail(f"rule {EXPECTED_RULE_ID} not present in rules_executed")
        failures += 1
    elif a1_record.status.value == "fired":
        _ok(f"{EXPECTED_RULE_ID} status=fired")
    else:
        _fail(f"{EXPECTED_RULE_ID} expected status=fired, got {a1_record.status.value}")
        failures += 1

    print()
    if failures:
        print(f"DEMO FAILED: {failures} assertion(s) did not hold.", file=sys.stderr)
        return 1
    print("DEMO GREEN: W7 A1 acceptance contract satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
