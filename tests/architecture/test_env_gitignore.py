"""W13-9 architecture regression: `.env` files are gitignored, `.env.example`
is tracked.

The repo carries secrets via per-developer `.env` files but commits a
sanitised template at `.env.example`. The pattern is enforced in
`.gitignore` with three contributing rules:

  - `.gitignore:8`  `*.env`         — wildcard sweep for any `*.env` filename
  - `.gitignore:45` `.env`           — explicit pin on the canonical name
  - `.gitignore:46` `!.env.example`  — negative exception so the template stays

§11.10 (`REFACTOR_OPTIMIZATION.md`) goal: regression gate for the
`.env` rule. Until W13-9 there was no architecture test pinning these
invariants, so a future drift on line 8/45/46 could land silently.
This module exercises `git check-ignore` against a curated set of
paths and asserts the expected ignore/track classification.

Paths exercised:
  - Repo-root `.env` (ignored via line 45 literal, plus line 8 wildcard).
  - Arbitrary `*.env` filenames at repo root (`foo.env`, `bar.env`)
    — ignored via line 8 wildcard.
  - Nested `subdir/.env` paths — ignored via line 45 literal (gitignore
    matches in any subdirectory unless anchored).
  - `.env.example` at repo root — tracked (line 46 negative exception).
  - Common virtualenv directories (`.venv/`, `env/`, `venv/`) — ignored.

`git check-ignore` exit codes (man gitignore(5), git-check-ignore(1)):
  0 = path is ignored
  1 = path is NOT ignored
  128 = error
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]


def _resolve_git_binary() -> str:
    """Resolve the absolute path of `git`.

    Ruff S607 (partial-executable-path) disallows bare-binary subprocess
    invocations; resolve the binary via `shutil.which()` so the test
    matches the project's W8-4 absolute-path policy. Skip the test if
    `git` is unavailable on PATH (CI sandboxes without git are not in
    scope for this regression gate).
    """
    git_bin = shutil.which("git")
    if git_bin is None:
        pytest.skip("git binary unavailable on PATH")
    return git_bin


def _is_ignored(path: str) -> bool:
    """Return True if `git check-ignore` reports `path` as ignored.

    `path` is interpreted relative to REPO_ROOT (the working tree root).
    The file does not have to exist — `git check-ignore` consults
    `.gitignore` semantics only, not the filesystem.
    """
    git_bin = _resolve_git_binary()
    result = subprocess.run(  # noqa: S603
        [git_bin, "check-ignore", "--no-index", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise AssertionError(
        f"git check-ignore failed for {path!r}: "
        f"returncode={result.returncode} stderr={result.stderr.strip()!r}"
    )


@pytest.mark.parametrize(
    "path",
    [
        # `.env` rules (lines 8, 45).
        ".env",
        "foo.env",
        "bar.env",
        "subdir/.env",
        "nested/deeper/.env",
        # Virtualenv dir rules (lines 5-7). Tested via paths inside each
        # directory so the directory-only `env/` / `venv/` / `.venv/`
        # semantics apply regardless of whether the dir exists on disk
        # at test-time (`git check-ignore --no-index` consults rules,
        # not the filesystem, but its dir-vs-file inference for the
        # query path itself does depend on whether the path exists).
        ".venv/lib/python3.12/site-packages/foo.py",
        "env/bin/python",
        "venv/bin/activate",
    ],
)
def test_secret_bearing_paths_are_gitignored(path: str) -> None:
    """W13-9 — `.env` files and virtualenv trees must be gitignored.

    Line 8 (`*.env`) covers arbitrary `*.env` filenames; line 45 (`.env`)
    pins the canonical name; lines 5-7 (`.venv/`, `env/`, `venv/`) cover
    virtualenv conventions. Any drift on these rules would let a
    developer accidentally commit a populated `.env` or stage a
    virtualenv tree.
    """
    assert _is_ignored(path), (
        f"{path!r} should be gitignored but `git check-ignore` reports it "
        f"as tracked. Check .gitignore lines 5-8, 45-46."
    )


def test_dotenv_example_template_is_tracked() -> None:
    """W13-9 — `.env.example` must stay tracked via the negative exception.

    `.gitignore:46` carries `!.env.example`, which overrides the
    `*.env` wildcard at line 8 and the explicit `.env` literal at
    line 45. The template documents required env vars (DATABASE_URL,
    API_HOST, etc.) for new contributors; if the negative exception
    drifts, the template silently stops landing in commits and
    onboarding breaks.
    """
    assert not _is_ignored(".env.example"), (
        ".env.example must remain tracked (negative exception at "
        ".gitignore:46). It was reported as gitignored — check that "
        "`!.env.example` is present and follows the `*.env` / `.env` "
        "rules so the negation actually applies."
    )


def test_dotenv_example_file_actually_exists_in_tree() -> None:
    """W13-9 — `.env.example` must be present in the working tree.

    The negative-exception rule at `.gitignore:46` only matters if the
    template file actually exists for `git add` to pick up. If
    `.env.example` is accidentally deleted, the regression gate above
    still passes (the rule is correct), but onboarding silently breaks.
    """
    template = REPO_ROOT / ".env.example"
    assert template.is_file(), (
        f"{template} must exist as the canonical env template "
        "(referenced by README onboarding + new-developer setup; "
        "see .gitignore:46 negative exception)."
    )
