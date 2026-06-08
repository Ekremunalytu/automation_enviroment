"""Architecture guards for the air-gapped Podman deployment bundle.

The Podman path is an operational packaging surface, so these tests stay
structural: they do not build images or require Podman on the dev host. They
pin the contracts that let the existing Docker-oriented API orchestrator run
unchanged against a rootful Podman socket on the target Fedora Server.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PODMAN_DIR = REPO_ROOT / "deploy" / "podman"
BUILD_SCRIPT = PODMAN_DIR / "build-bundle.sh"
CTL_SCRIPT = PODMAN_DIR / "extrace-ctl.sh"
README = PODMAN_DIR / "README.md"

_IMAGE_VARS = ("IMG_API", "IMG_EXECUTOR", "IMG_STATIC", "IMG_UI", "IMG_PG")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assignment_map(script: Path) -> dict[str, str]:
    text = _read(script)
    found: dict[str, str] = {}
    for name in _IMAGE_VARS:
        match = re.search(rf'^{name}="([^"]+)"$', text, re.MULTILINE)
        assert match, f"{script.relative_to(REPO_ROOT)} missing {name} assignment"
        found[name] = match.group(1)
    return found


def _block_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


@pytest.mark.parametrize("script", (BUILD_SCRIPT, CTL_SCRIPT))
def test_podman_shell_scripts_parse(script: Path) -> None:
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", "-n", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{script.relative_to(REPO_ROOT)} must parse with bash -n.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_bundle_builder_and_controller_use_same_image_contract() -> None:
    assert _assignment_map(BUILD_SCRIPT) == _assignment_map(CTL_SCRIPT)


def test_bundle_builder_creates_clean_self_contained_payload() -> None:
    text = _read(BUILD_SCRIPT)
    assert 'rm -rf "$STAGING"' in text, (
        "bundle staging must be cleaned before assembly so stale files from a "
        "previous build cannot enter the air-gapped tarball"
    )
    for token in (
        'cp "$HERE/extrace-ctl.sh" "$STAGING/extrace-ctl.sh"',
        'cp "$HERE/README.md" "$STAGING/README.md"',
        'cp "$REPO/.env.example" "$STAGING/extrace.env"',
        'tar -C "$STAGING" -czf "$BUNDLE" .',
    ):
        assert token in text


def test_controller_defaults_to_rootful_loopback_podman() -> None:
    text = _read(CTL_SCRIPT)
    assert 'EXTRACE_BIND="${EXTRACE_BIND:-127.0.0.1}"' in text
    assert 'PODMAN_SOCK="${PODMAN_SOCK:-/run/podman/podman.sock}"' in text
    assert '[ "$(id -u)" = "0" ]' in text
    assert 'die "run as root (rootful podman): sudo $0 $*"' in text


def test_controller_keeps_runtime_container_name_contracts() -> None:
    text = _read(CTL_SCRIPT)
    expected = {
        'C_DB="automation_db"',
        'C_API="automation_api"',
        'C_EXEC="automation_executor"',
        'C_STATIC="automation_static_analyzer"',
        'C_UI="automation_ui"',
    }
    missing = sorted(token for token in expected if token not in text)
    assert not missing, (
        "Podman controller container names must match executor/config.py and "
        f"docker-compose.yml contracts. Missing: {missing}"
    )


def test_controller_mounts_rootful_podman_socket_as_docker_sock() -> None:
    text = _read(CTL_SCRIPT)
    api_block = _block_between(text, "# --- api", "# --- executor")
    assert '-v "${PODMAN_SOCK}:/var/run/docker.sock"' in api_block
    assert "--security-opt label=disable" in api_block
    assert "--security-opt no-new-privileges=true" in api_block


def test_controller_preserves_sandbox_isolation_posture() -> None:
    text = _read(CTL_SCRIPT)
    executor_block = _block_between(text, "# --- executor", "# --- static analyzer")
    static_block = _block_between(text, "# --- static analyzer", "# --- ui")
    assert "-e EXECUTOR_CDP_PORT=" in executor_block
    assert "--cap-drop ALL --cap-add NET_RAW --cap-add SYS_PTRACE" in executor_block
    assert "--network none" in static_block
    assert "--cap-drop ALL" in static_block
    assert ":/extensions-input:ro,z" in static_block


@pytest.mark.parametrize("function_name", ("status", "logs", "exec", "migrate"))
def test_operator_commands_stay_in_rootful_podman_context(function_name: str) -> None:
    text = _read(CTL_SCRIPT)
    match = re.search(
        rf"cmd_{function_name}\(\) \{{(?P<body>.*?)\n\}}",
        text,
        re.DOTALL,
    )
    assert match, f"cmd_{function_name} function missing"
    body = match.group("body")
    assert f"need_root {function_name}" in body
    assert "have_podman" in body


def test_podman_readme_documents_operator_safety_contracts() -> None:
    text = _read(README)
    for token in (
        "headless, air-gapped x86 Fedora Server",
        "rootful",
        "Default binding is **loopback only**",
        "Prefer an SSH tunnel over LAN exposure",
        "Rootless Podman",
        "postgres_test",
        "executor-cdp",
    ):
        assert token in text
