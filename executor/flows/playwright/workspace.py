"""Filesystem workspace helpers (pathlib-based, no Playwright)."""

from __future__ import annotations

import shutil
import stat
from pathlib import Path

from language_samples import _LANGUAGE_SAMPLE_FILES, _WORKSPACE_PATTERN_FILES
from workspace_seed_data import HOME_FILES, LANGUAGE_EXTENSIONS, WORKSPACE_FILES

WORKSPACE_DIR = Path("/workspace")
HOME_DIR = Path("/home/executor")


def create_workspace_file(filename: str, content: str = "") -> Path:
    """Create a file inside the workspace directory."""
    path = WORKSPACE_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def create_workspace_dir(dirname: str) -> Path:
    """Create a directory inside the workspace."""
    path = WORKSPACE_DIR / dirname
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_language_file(language_id: str) -> Path:
    """Create a sample file for a given VS Code language ID."""
    return create_workspace_file(f"sample{LANGUAGE_EXTENSIONS[language_id]}")


def create_workspace_structure(files: dict[str, str]) -> list[Path]:
    """Create multiple files at once."""
    return [create_workspace_file(name, content) for name, content in files.items()]


def create_bait_files(filenames: list[str]) -> list[Path]:
    """Create empty bait files inside the active workspace."""
    created_files: list[Path] = []
    for name in filenames:
        bait_path = WORKSPACE_DIR / name
        bait_path.parent.mkdir(parents=True, exist_ok=True)
        if not bait_path.exists():
            bait_path.write_text("")
        created_files.append(bait_path)
    return created_files


def clean_workspace() -> None:
    """Remove all contents of the workspace directory."""
    for child in WORKSPACE_DIR.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def setup_dev_environment() -> None:
    """Create a realistic developer honeypot environment."""
    create_workspace_structure(WORKSPACE_FILES)
    create_workspace_structure(_LANGUAGE_SAMPLE_FILES)
    create_workspace_structure(_WORKSPACE_PATTERN_FILES)

    for script in ["scripts/deploy.sh", "scripts/backup.sh", "scripts/migrate.rb"]:
        path = WORKSPACE_DIR / script
        if path.exists():
            path.chmod(path.stat().st_mode | stat.S_IEXEC)

    for rel_path, content in HOME_FILES.items():
        path = HOME_DIR / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    ssh_key = HOME_DIR / ".ssh" / "id_rsa"
    if ssh_key.exists():
        ssh_key.chmod(0o600)
    ssh_dir = HOME_DIR / ".ssh"
    if ssh_dir.exists():
        ssh_dir.chmod(0o700)


if __name__ == "__main__":
    print("[*] Setting up developer environment...")
    setup_dev_environment()
    print("[+] Environment ready: .env, SSH keys, AWS creds, source code, etc.")
