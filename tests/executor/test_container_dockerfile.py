from __future__ import annotations

from pathlib import Path


_EXPECTED_BASE_IMAGE = (
    "ubuntu:22.04@sha256:"
    "962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7"
)


def test_executor_dockerfile_pins_base_image_digest() -> None:
    dockerfile = (
        Path(__file__).resolve().parents[2] / "executor" / "container" / "Dockerfile"
    )
    first_from = next(
        line.strip()
        for line in dockerfile.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("FROM ")
    )

    assert "@sha256:" in first_from
    assert first_from == f"FROM {_EXPECTED_BASE_IMAGE}"


def test_executor_dockerfile_sanitizes_vscode_build_args() -> None:
    dockerfile = (
        Path(__file__).resolve().parents[2] / "executor" / "container" / "Dockerfile"
    )
    content = dockerfile.read_text(encoding="utf-8")

    assert 'VSCODE_CHANNEL="$(printf \'%s\' "${EXECUTOR_VSCODE_CHANNEL}"' in content
    assert 'VSCODE_VERSION="$(printf \'%s\' "${EXECUTOR_VSCODE_VERSION}"' in content
    assert "contains embedded whitespace" in content
    assert (
        "https://update.code.visualstudio.com/"
        "${VSCODE_VERSION}/${VSCODE_ARCH}/${VSCODE_CHANNEL}"
    ) in content
