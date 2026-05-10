from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE_ROOTS = (
    ROOT / "docker",
    ROOT / "executor" / "container",
    ROOT / "ui",
)


def _dockerfiles() -> list[Path]:
    files: list[Path] = []
    for root in DOCKERFILE_ROOTS:
        files.extend(path for path in root.rglob("Dockerfile") if path.is_file())
    return sorted(files)


def test_all_runtime_dockerfiles_pin_base_images_by_digest() -> None:
    """ADR 0002 trust boundary: every runtime Dockerfile base image is pinned."""

    dockerfiles = _dockerfiles()
    assert dockerfiles

    offenders: list[str] = []
    for dockerfile in dockerfiles:
        for line_no, line in enumerate(
            dockerfile.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            stripped = line.strip()
            if not stripped.startswith("FROM "):
                continue
            image = stripped.split()[1]
            if image == "scratch":
                continue
            if "@sha256:" not in image:
                rel = dockerfile.relative_to(ROOT)
                offenders.append(f"{rel}:{line_no}: {stripped}")

    assert offenders == []
