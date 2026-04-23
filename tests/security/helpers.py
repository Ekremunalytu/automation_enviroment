from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from appcore.contracts.schemas import AnalysisBundle
from workflows.marketplace.analysis_service import run_local_analysis

REPO_ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_ROOT = REPO_ROOT / "extensions" / "malicious"
_FIXTURE_REPORTS = {
    "extrace.fixture-chat-0.0.1": (
        REPO_ROOT
        / "tests"
        / "platform"
        / "contracts"
        / "fixtures"
        / "activation_reports"
        / "extrace_fixture_chat.json"
    ),
    "extrace.fixture-theme-0.0.1": (
        REPO_ROOT
        / "tests"
        / "platform"
        / "contracts"
        / "fixtures"
        / "activation_reports"
        / "extrace_fixture_theme.json"
    ),
}


def load_manifest(fixture_dir: Path) -> dict[str, object]:
    return json.loads((fixture_dir / "LABEL.yaml").read_text(encoding="utf-8"))


def analyze_fixture(fixture_dir: Path) -> AnalysisBundle:
    report_path = fixture_dir / "activation_report.json"
    if report_path.exists():
        return run_local_analysis(fixture_dir)

    fallback_report = _FIXTURE_REPORTS.get(fixture_dir.name)
    if fallback_report is None:
        raise FileNotFoundError(
            f"No offline activation report fixture found for {fixture_dir}."
        )

    with tempfile.TemporaryDirectory(
        prefix=f"{fixture_dir.name}-analysis-"
    ) as temp_dir:
        temp_fixture_dir = Path(temp_dir) / fixture_dir.name
        temp_fixture_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fixture_dir / "package.json", temp_fixture_dir / "package.json")
        shutil.copy2(fallback_report, temp_fixture_dir / "activation_report.json")
        return run_local_analysis(temp_fixture_dir)


def production_rule_ids(bundle: AnalysisBundle) -> set[str]:
    return {finding.rule_id for finding in bundle.detection_report.findings}
