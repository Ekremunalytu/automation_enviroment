"""W14 close-out: every fenced code block in ``documents/adrs/*.md``
must carry a language info string.

ADRs are the authoritative narrative for cross-cutting decisions (CDP
posture, executor fingerprint, logger consolidation, etc.). Bare ```
blocks degrade syntax-highlighting in renderers, signal sloppy
authorship, and (more importantly) slip past the pre-commit
``markdownlint`` hook when it runs with ``--fix`` — the auto-fix
rewrites blocks in place without warning. The W14 post-Codex review
caught two such bare fences in ADR 0009 (CDP-default-disabled) that
had survived multiple commits.

This gate enforces the rule **locally to ADRs** (the rest of the
repo is covered by markdownlint MD040 via ``make markdownlint`` /
``.pre-commit-config.yaml``). Running here means the regression
trips even if the markdownlint posture changes (e.g. someone
re-introduces ``--fix`` or weakens the rule set).

Pattern modeled on the W14-7.b container-shipping regression test and
W14-8 Python 3.11+ API guard.
"""

from __future__ import annotations

from pathlib import Path

ADR_DIR = Path(__file__).resolve().parents[2] / "documents" / "adrs"


def _bare_opening_fences(text: str) -> list[int]:
    r"""Return 1-indexed line numbers of opening fences without language.

    Walks lines linearly, toggling an ``inside`` flag at each fence line.
    The opener is the line where ``inside`` flips from False to True; a
    bare opener is exactly three backticks alone on the line (after
    stripping). Closers are ignored. Tilde fences (``~~~``) are not
    considered — ADRs use backtick fences by convention.
    """
    lines = text.splitlines()
    inside = False
    bare_openers: list[int] = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("```"):
            continue
        if inside:
            inside = False
            continue
        inside = True
        if stripped == "```":
            bare_openers.append(i)
    return bare_openers


def test_adr_code_fences_carry_language() -> None:
    violations: list[str] = []
    repo_root = ADR_DIR.parent.parent
    for adr_path in sorted(ADR_DIR.glob("*.md")):
        if adr_path.name.lower().startswith("readme"):
            continue
        text = adr_path.read_text(encoding="utf-8")
        for lineno in _bare_opening_fences(text):
            violations.append(f"{adr_path.relative_to(repo_root)}:{lineno}")
    assert not violations, (
        "ADR fenced code blocks must carry a language info string "
        "(e.g. ```text, ```python, ```bash, ```yaml). Bare ``` openers "
        "found at:\n  " + "\n  ".join(violations)
    )
