"""Tests for the offline-intake endpoints.

``GET /api/marketplace/offline/list`` and ``POST /api/marketplace/offline/ingest``
are the air-gapped twins of marketplace search/download: the operator drops
raw ``.vsix`` files into ``settings.project.OFFLINE_DIR`` and the API scans /
stages them through the same hardened extract path. DB writes are mocked via
the shared ``client`` fixture; thresholds are stubbed to the module fallbacks.
"""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from appcore.api.config import settings
from packages.marketplace_identity import safe_marketplace_slug
from workflows.marketplace import client as marketplace_client


def _make_vsix(
    publisher: str = "ms-python",
    name: str = "python",
    version: str = "2025.0.0",
    *,
    display_name: str = "Python",
    description: str = "Python tooling.",
    extra_files: dict[str, str] | None = None,
) -> bytes:
    manifest = {
        "publisher": publisher,
        "name": name,
        "version": version,
        "displayName": display_name,
        "description": description,
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("extension/package.json", json.dumps(manifest))
        zf.writestr("extension/extension.js", "console.log('ok')")
        for entry, content in (extra_files or {}).items():
            zf.writestr(entry, content)
    return archive.getvalue()


@pytest.fixture
def offline_dirs(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    """Point OFFLINE_DIR + EXTENSION_DIR at isolated temp dirs."""
    offline_dir = tmp_path / "offline"
    extension_dir = tmp_path / "extensions"
    offline_dir.mkdir()
    extension_dir.mkdir()
    monkeypatch.setattr(settings.project, "OFFLINE_DIR", str(offline_dir))
    monkeypatch.setattr(settings.project, "EXTENSION_DIR", str(extension_dir))
    return offline_dir, extension_dir


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_offline_empty_returns_empty_list(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    response = client.get("/api/marketplace/offline/list")
    assert response.status_code == 200
    assert response.json() == []


def test_list_offline_reads_identity_from_manifest(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    offline_dir, _ = offline_dirs
    # Deliberately mismatched on-disk filename — identity must come from the
    # in-archive manifest, not the filename.
    (offline_dir / "renamed.vsix").write_bytes(_make_vsix())

    response = client.get("/api/marketplace/offline/list")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    record = body[0]
    assert record["publisher"] == "ms-python"
    assert record["name"] == "python"
    assert record["version"] == "2025.0.0"
    assert record["displayName"] == "Python"
    assert record["filename"] == "renamed.vsix"
    assert record["size_bytes"] > 0
    assert record["already_ingested"] is False


def test_list_offline_marks_already_ingested(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    offline_dir, extension_dir = offline_dirs
    (offline_dir / "python.vsix").write_bytes(_make_vsix())

    # Stage the extracted dir + canonical .vsix so it reads as ingested.
    slug = safe_marketplace_slug("ms-python", "python", "2025.0.0")
    staged = extension_dir / slug
    staged.mkdir()
    (staged / "package.json").write_text('{"name": "python"}', encoding="utf-8")
    (extension_dir / f"{slug}.vsix").write_bytes(b"vsix")

    response = client.get("/api/marketplace/offline/list")
    assert response.json()[0]["already_ingested"] is True


def test_list_offline_skips_unreadable_archive(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    offline_dir, _ = offline_dirs
    (offline_dir / "broken.vsix").write_bytes(b"not a zip")
    (offline_dir / "good.vsix").write_bytes(_make_vsix())

    body = client.get("/api/marketplace/offline/list").json()
    assert [r["filename"] for r in body] == ["good.vsix"]


def test_list_offline_skips_oversize_archive(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    """F-2: an archive whose on-disk size exceeds ``vsix_max_uncompressed_size``
    is skipped before ``read_bytes()`` so it cannot exhaust memory mid-scan —
    the in-budget package is still listed."""
    offline_dir, _ = offline_dirs
    (offline_dir / "good.vsix").write_bytes(_make_vsix())
    (offline_dir / "huge.vsix").write_bytes(b"x" * 50_000)

    with patch(
        "workflows.marketplace.router._resolve_max_uncompressed_size",
        return_value=10_000,
    ):
        body = client.get("/api/marketplace/offline/list").json()

    assert [r["filename"] for r in body] == ["good.vsix"]


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------


def test_ingest_offline_success_stages_and_registers(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    offline_dir, extension_dir = offline_dirs
    (offline_dir / "python.vsix").write_bytes(_make_vsix())

    mock_ext = MagicMock()
    mock_ext.id = 7

    with (
        patch(
            "workflows.security_settings.load_vsix_thresholds",
            return_value={},
        ),
        patch(
            "workflows.marketplace.router.create_extension_from_directory",
            return_value=mock_ext,
        ),
    ):
        response = client.post(
            "/api/marketplace/offline/ingest",
            json={"filename": "python.vsix"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["publisher"] == "ms-python"
    assert body["db_id"] == 7
    assert "ingested from offline" in body["message"]
    assert body["vsix_metrics"]["file_count"] >= 1

    slug = safe_marketplace_slug("ms-python", "python", "2025.0.0")
    assert (extension_dir / slug / "package.json").exists()
    assert (extension_dir / f"{slug}.vsix").exists()


def test_ingest_offline_rejects_path_traversal_filename(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    response = client.post(
        "/api/marketplace/offline/ingest",
        json={"filename": "../secrets.vsix"},
    )
    assert response.status_code == 400


def test_ingest_offline_missing_file_returns_404(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    response = client.post(
        "/api/marketplace/offline/ingest",
        json={"filename": "absent.vsix"},
    )
    assert response.status_code == 404


def test_ingest_offline_bad_zip_returns_422(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    offline_dir, _ = offline_dirs
    (offline_dir / "broken.vsix").write_bytes(b"not a zip")

    response = client.post(
        "/api/marketplace/offline/ingest",
        json={"filename": "broken.vsix"},
    )
    assert response.status_code == 422


def test_ingest_offline_unsafe_manifest_identity_returns_422(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    """A manifest whose identity violates slug discipline (path-traversal in
    ``publisher``) is rejected before any bytes touch the extension store."""
    offline_dir, extension_dir = offline_dirs
    (offline_dir / "evil.vsix").write_bytes(
        _make_vsix(publisher="../../etc", name="python", version="1.0.0")
    )

    response = client.post(
        "/api/marketplace/offline/ingest",
        json={"filename": "evil.vsix"},
    )
    assert response.status_code == 422
    # Nothing was extracted.
    assert not any(extension_dir.iterdir())


def test_ingest_offline_threshold_breach_returns_structured_422(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    """A breach during extraction maps to the same structured 422 the UI
    popup consumes, identical to the download path."""
    offline_dir, _ = offline_dirs
    (offline_dir / "python.vsix").write_bytes(_make_vsix())

    err = marketplace_client.VSIXUnpackError(
        "VSIX archive exceeds entry count limit (50000)",
        breach_kind=marketplace_client.VSIX_BREACH_ENTRY_COUNT,
        threshold_name="vsix_max_file_count",
        threshold_value=50_000,
        observed_value=50_001,
    )

    with patch(
        "workflows.marketplace.client.persist_and_extract_vsix_bytes",
        side_effect=err,
    ):
        response = client.post(
            "/api/marketplace/offline/ingest",
            json={"filename": "python.vsix"},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "vsix_threshold_breach"
    assert detail["breach_kind"] == "entry_count"
    assert detail["publisher"] == "ms-python"


def test_ingest_offline_oversize_rejected_before_read_returns_structured_422(
    client: TestClient, offline_dirs: tuple[Path, Path]
) -> None:
    """F-2: an over-limit archive is rejected by the pre-read size gate
    *before* ``read_bytes()`` pulls it into memory, and surfaces the same
    structured 422 as an extraction-time breach.

    The dropped file is deliberately NOT a valid zip: if the size gate fired
    before the read + zip parse (as F-2 requires) we get the structured
    ``uncompressed_size`` breach; had the bytes been read and parsed first we
    would instead get a bad-zip 422. The breach_kind therefore proves the
    pre-read ordering. Identity is unknown pre-manifest, so the filename
    stands in for the package name."""
    offline_dir, _ = offline_dirs
    oversize = b"x" * 50_000
    (offline_dir / "huge.vsix").write_bytes(oversize)

    with patch(
        "workflows.marketplace.router._resolve_max_uncompressed_size",
        return_value=10_000,
    ):
        response = client.post(
            "/api/marketplace/offline/ingest",
            json={"filename": "huge.vsix"},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "vsix_threshold_breach"
    assert detail["breach_kind"] == "uncompressed_size"
    assert detail["threshold_name"] == "vsix_max_uncompressed_size"
    assert detail["threshold_value"] == 10_000
    assert detail["observed_value"] == len(oversize)
    assert detail["name"] == "huge.vsix"


def test_read_offline_vsix_oversize_raises_before_read(
    offline_dirs: tuple[Path, Path],
) -> None:
    """F-2 unit contract: ``read_offline_vsix`` raises the structured
    ``VSIXUnpackError`` (not a ``BadZipFile``) when the on-disk size exceeds
    the cap, proving the gate fires before ``read_bytes()`` + the zip parse.
    The dropped bytes are deliberately not a valid zip; an
    ``uncompressed_size`` breach (rather than a zip-parse error) is the
    proof of ordering, independent of the router."""
    from workflows.marketplace import offline as offline_intake

    offline_dir, _ = offline_dirs
    (offline_dir / "huge.vsix").write_bytes(b"x" * 50_000)

    with pytest.raises(marketplace_client.VSIXUnpackError) as excinfo:
        offline_intake.read_offline_vsix("huge.vsix", max_uncompressed_size=10_000)

    exc = excinfo.value
    assert exc.breach_kind == marketplace_client.VSIX_BREACH_UNCOMPRESSED_SIZE
    assert exc.threshold_name == "vsix_max_uncompressed_size"
    assert exc.threshold_value == 10_000
    assert exc.observed_value == 50_000
