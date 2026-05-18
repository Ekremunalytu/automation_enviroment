from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE_ROOTS = (
    ROOT / "docker",
    ROOT / "executor" / "container",
    ROOT / "ui",
)
COMPOSE_FILES = (ROOT / "docker-compose.yml",)
_COMPOSE_IMAGE_RE = re.compile(r"^\s*image:\s*(\S+)\s*$")


def _dockerfiles() -> list[Path]:
    files: list[Path] = []
    for root in DOCKERFILE_ROOTS:
        files.extend(path for path in root.rglob("Dockerfile") if path.is_file())
    return sorted(files)


def _compose_image_lines(path: Path) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        match = _COMPOSE_IMAGE_RE.match(line)
        if match is None:
            continue
        out.append((line_no, line.strip(), match.group(1)))
    return out


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


def test_compose_image_refs_pin_by_digest() -> None:
    """ADR 0002 trust boundary extends to docker-compose image: keys (W15-7)."""

    offenders: list[str] = []
    for compose_path in COMPOSE_FILES:
        if not compose_path.is_file():
            continue
        for line_no, stripped, image_ref in _compose_image_lines(compose_path):
            if "@sha256:" not in image_ref:
                rel = compose_path.relative_to(ROOT)
                offenders.append(f"{rel}:{line_no}: {stripped}")

    assert offenders == [], (
        "compose image: keys must be digest-pinned per ADR 0002 §4 "
        f"(Trust Boundaries → Docker base image). Offenders: {offenders}"
    )


def test_compose_files_tuple_resolves_to_existing_paths() -> None:
    """COMPOSE_FILES must point at real files so the gate cannot silently no-op."""

    missing = [str(p) for p in COMPOSE_FILES if not p.is_file()]
    assert not missing, (
        f"COMPOSE_FILES tuple references non-existent paths: {missing}. "
        "Update the tuple to reflect renames/moves so the digest-pin gate "
        "does not silently pass on an empty input set."
    )
