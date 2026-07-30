"""Prevent canonical and default agent-context documents from regrowing."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# doc -> hard ceiling in estimated tokens (wc -w * 1.3).
_CEILINGS: dict[str, int] = {
    "documents/REFACTOR_OPTIMIZATION.md": 3000,
    "documents/REFACTOR_STATUS.md": 2500,
    "documents/POST_POC_BACKLOG.md": 18500,
}

_ENTRY_BASE_PATHS = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "documents" / "AGENT_CONTEXT.md",
    REPO_ROOT / "documents" / "README.md",
)
_ENTRY_LANES = tuple(
    path
    for path in sorted((REPO_ROOT / "documents" / "agent-lanes").glob("*.md"))
    if path.name != "README.md"
)
_ENTRY_PATH_CEILING = 3000


def _estimated_tokens(path: Path) -> int:
    return int(len(path.read_text(encoding="utf-8").split()) * 1.3)


@pytest.mark.parametrize("rel_path, ceiling", sorted(_CEILINGS.items()))
def test_slim_canonical_under_token_ceiling(rel_path: str, ceiling: int) -> None:
    path = REPO_ROOT / rel_path
    assert path.is_file(), f"budget-gated doc missing: {rel_path}"
    tokens = _estimated_tokens(path)
    assert tokens <= ceiling, (
        f"{rel_path} is ~{tokens} tokens, over its {ceiling}-token ceiling. "
        f"The slim canonical regrew — snapshot the closed/verbose content to a "
        f"dated `archive/` file and re-trim to a pointer (see "
        f"`documents/agent-lanes/docs-maintenance.md` §Archive + Active-Work "
        f"Discipline). Do not drop stable-ID tokens from POST_POC_BACKLOG.md."
    )


@pytest.mark.parametrize("lane", _ENTRY_LANES, ids=lambda path: path.stem)
def test_default_agent_entry_path_under_token_ceiling(lane: Path) -> None:
    """AGENTS + pointers + one lane must stay within the documented budget."""
    paths = (*_ENTRY_BASE_PATHS, lane)
    tokens = int(
        sum(len(path.read_text(encoding="utf-8").split()) for path in paths) * 1.3
    )
    assert tokens <= _ENTRY_PATH_CEILING, (
        f"Default entry path through {lane.name} is ~{tokens} tokens, over the "
        f"{_ENTRY_PATH_CEILING}-token ceiling. Remove duplicated state or move "
        "detail behind a task-specific pointer."
    )
