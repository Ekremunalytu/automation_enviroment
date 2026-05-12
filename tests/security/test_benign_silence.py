from __future__ import annotations

from tests.security.helpers import REPO_ROOT, analyze_fixture


def test_benign_chat_fixture_remains_silent() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-chat-0.0.1")

    assert bundle.detection_report.findings == []
    assert bundle.detection_report.verdict == "clean"


def test_benign_theme_fixture_remains_silent() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-theme-0.0.1")

    assert bundle.detection_report.findings == []
    assert bundle.detection_report.verdict == "clean"


def test_benign_snippet_fixture_remains_silent() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-snippet-0.0.1")

    assert bundle.detection_report.findings == []
    assert bundle.detection_report.verdict == "clean"


def test_benign_keybinding_fixture_remains_silent() -> None:
    bundle = analyze_fixture(
        REPO_ROOT / "extensions" / "extrace.fixture-keybinding-0.0.1"
    )

    assert bundle.detection_report.findings == []
    assert bundle.detection_report.verdict == "clean"


def test_benign_cmd_fixture_remains_silent() -> None:
    bundle = analyze_fixture(REPO_ROOT / "extensions" / "extrace.fixture-cmd-0.0.1")

    assert bundle.detection_report.findings == []
    assert bundle.detection_report.verdict == "clean"
