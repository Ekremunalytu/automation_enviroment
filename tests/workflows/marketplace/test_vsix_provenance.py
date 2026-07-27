"""W26 / Stream 3 (S7): B5 provenance tests.

B5: the analyzed-bytes hash distinguishes byte-different VSIX (not conflated),
is stamped on the static report, flows through the dynamic emit boundary to the
top-level on-disk key, and the orchestrator log-checks dynamic/static agreement.
B6 reproducibility is pinned at the stop() level in
``tests/executor/test_playwright_monitor_lifecycle.py``
(``test_stop_binds_signal_summary_verdict_to_frozen_snapshot`` — the verdict
reads the frozen snapshot) plus ``test_log_capture_health_snapshot`` and
``test_run_quality_partition``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import workflows.marketplace.analysis_service as analysis_service
from executor.flows.playwright.monitor.types import ActivationReport
from static_runtime.static_runner import run_static_detection_engine
from workflows.marketplace.client import compute_vsix_sha256


# ---- B5: compute_vsix_sha256 — byte-bound, not conflated --------------------


def test_compute_vsix_sha256_deterministic_and_byte_distinguishing(
    tmp_path: Path,
) -> None:
    a = tmp_path / "a.vsix"
    a.write_bytes(b"same-bytes-payload")
    a_again = tmp_path / "a_again.vsix"
    a_again.write_bytes(b"same-bytes-payload")
    b = tmp_path / "b.vsix"  # same "version", one byte different
    b.write_bytes(b"same-bytes-payloaD")

    digest = compute_vsix_sha256(a)
    # Deterministic + binds to bytes (same bytes anywhere -> same hash).
    assert digest == compute_vsix_sha256(a)
    assert digest == compute_vsix_sha256(a_again)
    # Byte-different same-version archives are NOT conflated.
    assert digest != compute_vsix_sha256(b)
    # Canonical 64-char lowercase hex, matching the hashlib reference.
    assert len(digest) == 64
    assert digest == digest.lower()
    assert set(digest) <= set("0123456789abcdef")
    assert digest == hashlib.sha256(b"same-bytes-payload").hexdigest()


def test_compute_vsix_sha256_streams_large_input(tmp_path: Path) -> None:
    # Larger than the 64 KiB chunk so the streaming loop iterates.
    payload = b"\xab" * (64 * 1024 * 3 + 7)
    path = tmp_path / "big.vsix"
    path.write_bytes(payload)
    assert compute_vsix_sha256(path) == hashlib.sha256(payload).hexdigest()


# ---- B5: static report carries the hash -------------------------------------


def test_static_engine_stamps_vsix_sha256(tmp_path: Path) -> None:
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path),
        rules_version="1.0.0",
        timeout_budget_s=30,
        semgrep_enabled=False,
        vsix_sha256="c" * 64,
    )
    assert report.vsix_sha256 == "c" * 64


def test_static_engine_defaults_vsix_sha256_empty(tmp_path: Path) -> None:
    report = run_static_detection_engine(
        vsix_dir=str(tmp_path),
        rules_version="1.0.0",
        timeout_budget_s=30,
        semgrep_enabled=False,
    )
    assert report.vsix_sha256 == ""


# ---- B5: orchestrator agreement log-check -----------------------------------


def _capture_logger_errors(monkeypatch) -> list[tuple]:
    errors: list[tuple] = []
    monkeypatch.setattr(
        analysis_service.logger,
        "error",
        lambda *args, **kwargs: errors.append((args, kwargs)),
    )
    return errors


def test_agreement_logs_on_dynamic_stamp_mismatch(monkeypatch) -> None:
    errors = _capture_logger_errors(monkeypatch)
    analysis_service._check_vsix_provenance_agreement(
        expected="a" * 64,
        dynamic_payload={"vsix_sha256": "b" * 64},
        static_report=None,
    )
    assert errors, "a non-empty disagreeing dynamic stamp must log an ERROR"


def test_agreement_silent_when_stamps_match(monkeypatch) -> None:
    errors = _capture_logger_errors(monkeypatch)
    analysis_service._check_vsix_provenance_agreement(
        expected="a" * 64,
        dynamic_payload={"vsix_sha256": "a" * 64},
        static_report=None,
    )
    assert not errors


def test_agreement_skips_when_expected_empty(monkeypatch) -> None:
    errors = _capture_logger_errors(monkeypatch)
    analysis_service._check_vsix_provenance_agreement(
        expected="",
        dynamic_payload={"vsix_sha256": "b" * 64},
        static_report=None,
    )
    assert not errors


def test_agreement_tolerates_empty_producer_stamp(monkeypatch) -> None:
    # A producer that did not stamp (e.g. a skip path) is tolerated — only a
    # non-empty *different* stamp is a wiring defect.
    errors = _capture_logger_errors(monkeypatch)
    analysis_service._check_vsix_provenance_agreement(
        expected="a" * 64,
        dynamic_payload={"vsix_sha256": ""},
        static_report=None,
    )
    assert not errors


# ---- B5: dynamic producer stamps the hash through the emit boundary ---------


def test_dynamic_report_save_stamps_vsix_sha256_top_level_key(tmp_path: Path) -> None:
    # B5 (Tests-3): the dynamic emit boundary (report.save -> build_report_data ->
    # save_report_payload) stamps the threaded hash as the top-level "vsix_sha256"
    # key, and it survives the extra=forbid contract round-trip. This pins the
    # report -> on-disk key the orchestrator agreement check reads; a key/attribute
    # rename (which the dict-injecting agreement tests cannot catch) breaks it.
    report = ActivationReport()
    report.target_extension_id = "pub.ext"
    report.vsix_sha256 = "d" * 64
    out = report.save(tmp_path / "report.json", announce=False)
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    assert data["vsix_sha256"] == "d" * 64


def test_dynamic_report_save_defaults_vsix_sha256_empty(tmp_path: Path) -> None:
    # The unstamped path (legacy / skip) persists the empty-string sentinel the
    # agreement check tolerates — never a missing key (which extra=forbid + the
    # agreement read would mishandle).
    report = ActivationReport()
    report.target_extension_id = "pub.ext"
    out = report.save(tmp_path / "report.json", announce=False)
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    assert data["vsix_sha256"] == ""
