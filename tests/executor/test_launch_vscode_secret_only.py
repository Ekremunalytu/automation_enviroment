"""W19-X behavioral regression: ``launch_vscode.sh --secret-only`` env-var inheritance.

The W19-X reactivation race fix relies on every reload reactivation finding
a fresh HMAC secret on disk. To keep the secret value consistent across
reactivations within a single VS Code lifetime — so the Python verifier's
cached secret continues to match every signed marker — ``--secret-only``
mode MUST re-use ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` from the inherited
environment instead of minting a fresh random value (as the boot path does).
Generating a new value here would invalidate every signed marker the
reactivating Extension Host emits.

These cases invoke the real bash script as a subprocess against a tmp_path
sandbox, pinning the contract end-to-end without touching ``/run/extrace`` or
``/results``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCH_SCRIPT = REPO_ROOT / "executor" / "container" / "launch_vscode.sh"


def _run_secret_only(
    env_value: str | None,
    tmp_path: Path,
) -> tuple[int, str, Path, Path]:
    secret_path = tmp_path / "harness-secret"
    python_secret_path = tmp_path / "python-secret"

    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "EXECUTOR_HARNESS_SECRET_PATH": str(secret_path),
        "EXECUTOR_HARNESS_PYTHON_SECRET_PATH": str(python_secret_path),
    }
    if env_value is not None:
        env["EXECUTOR_HARNESS_PYTHON_SECRET_VALUE"] = env_value

    # arch-allow: bare-binary-path  # W19-X: test invokes the real launch script
    # under a hermetic env sandbox; PATH is constrained above and the script path
    # is built from REPO_ROOT.
    result = subprocess.run(  # noqa: S603
        ["bash", str(LAUNCH_SCRIPT), "--secret-only"],  # noqa: S607
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.returncode, result.stderr, secret_path, python_secret_path


def test_secret_only_fails_when_python_secret_value_env_unset(tmp_path: Path) -> None:
    """W19-X fail-closed: ``--secret-only`` without
    ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` must exit nonzero rather than
    fall back to generating a fresh random secret (which would invalidate
    every signed marker the reactivating Extension Host emits)."""
    rc, stderr, secret_path, python_secret_path = _run_secret_only(None, tmp_path)

    assert rc != 0, f"expected nonzero exit, got rc={rc}; stderr={stderr!r}"
    assert "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE" in stderr
    assert not secret_path.exists()
    assert not python_secret_path.exists()


def test_secret_only_writes_inherited_value_to_both_paths(tmp_path: Path) -> None:
    """W19-X core invariant: ``--secret-only`` re-uses the boot secret from
    the inherited env var so the Python verifier's cached value stays valid
    across every reload reactivation."""
    boot_secret = "a" * 64

    rc, stderr, secret_path, python_secret_path = _run_secret_only(
        boot_secret, tmp_path
    )

    assert rc == 0, f"expected zero exit, got rc={rc}; stderr={stderr!r}"
    assert secret_path.read_text() == boot_secret
    assert python_secret_path.read_text() == boot_secret


def test_secret_only_does_not_mint_a_fresh_random_secret(tmp_path: Path) -> None:
    """W19-X correctness regression: two consecutive ``--secret-only``
    invocations with the same inherited env value must write the same
    value, NOT two distinct random values (which would mismatch the
    Python verifier and cause unsigned-marker rejection)."""
    boot_secret = "b" * 64

    rc1, _, sp1, _ = _run_secret_only(boot_secret, tmp_path / "run1")
    rc2, _, sp2, _ = _run_secret_only(boot_secret, tmp_path / "run2")

    assert rc1 == 0
    assert rc2 == 0
    assert sp1.read_text() == sp2.read_text() == boot_secret


@pytest.mark.parametrize(
    "mode_octal,target",
    [(0o400, "harness"), (0o600, "python")],
)
def test_secret_only_preserves_chmod_per_path(
    tmp_path: Path, mode_octal: int, target: str
) -> None:
    """Mode invariants from W13-1: the harness path is 0400 (read-only by
    the extension owner) and the Python path is 0600 (host orchestration
    reads + unlinks). ``--secret-only`` must preserve these — otherwise a
    same-UID target could read the python path after rewrite."""
    boot_secret = "c" * 64

    rc, _, secret_path, python_secret_path = _run_secret_only(boot_secret, tmp_path)

    assert rc == 0
    target_path = secret_path if target == "harness" else python_secret_path
    actual_mode = target_path.stat().st_mode & 0o777
    assert actual_mode == mode_octal, (
        f"{target}: expected mode {mode_octal:o}, got {actual_mode:o}"
    )
