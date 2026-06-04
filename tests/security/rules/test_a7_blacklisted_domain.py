"""Fire / silent unit tests for the dynamic A7 blacklisted-domain rule.

The live-traffic leg of the ``blacklist_domains`` feature: an outbound network
event whose observed ``host`` resolves to a blacklisted registrable domain must
fire; benign or lookalike hosts must stay silent. Built over a synthetic
``ActivationReport`` (no sandbox), mirroring the a3 unit tests.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable

from packages.analysis_contracts import ActivationReport
from packages.analysis_engine.rules.a7_blacklisted_domain import RULE


def _report_with_hosts(hosts: Iterable[str]) -> ActivationReport:
    payload = {
        "report_version": 2,
        "target_extension_expected": "acme.thing",
        "automation_health": {"status": "healthy", "reasons": []},
        "signal_summary": {},
        "summary": {"target_extension_version": "0.0.1"},
        "scenario_traces": [],
        "evidence_events": [
            {
                "event_id": f"net-{index:04d}",
                "kind": "network",
                "rel_time_s": float(index),
                "summary": f"connect {host}",
                "host": host,
                "raw_context": {"event_class": "network", "event_type": "tls_sni"},
            }
            for index, host in enumerate(hosts)
        ],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
    }
    return ActivationReport.model_validate(copy.deepcopy(payload))


def test_fires_on_blacklisted_host() -> None:
    findings = RULE.evaluate(_report_with_hosts(["c2.evil.example"]))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.a7.blacklisted_domain"
    assert finding.severity.value == "high"
    assert finding.adversary_class.value == "A7"
    assert "evil.example" in finding.description
    assert finding.evidence, "finding must carry at least one evidence ref"


def test_fires_on_subdomain_of_blacklisted_domain() -> None:
    assert len(RULE.evaluate(_report_with_hosts(["a.b.exfil.example"]))) == 1


def test_silent_for_benign_host() -> None:
    assert RULE.evaluate(_report_with_hosts(["api.github.com"])) == []


def test_silent_for_lookalike_registrable_domain() -> None:
    assert RULE.evaluate(_report_with_hosts(["notevil.example"])) == []


def test_silent_for_no_network_events() -> None:
    assert RULE.evaluate(_report_with_hosts([])) == []


def test_fires_on_kagema_c2_host() -> None:
    # Regression: the kagema C2 (niggboo.com), a real curated entry on the shipped
    # seed denylist, is flagged when observed as an outbound host — exact match and
    # any subdomain. Guards against the entry being accidentally dropped.
    assert len(RULE.evaluate(_report_with_hosts(["niggboo.com"]))) == 1
    assert len(RULE.evaluate(_report_with_hosts(["stage2.niggboo.com"]))) == 1
