"""Slim-canonical token-budget ratchet gate.

The doc-preamble gates pin *consistency*; this gate pins *size*. The
``2026-06-15`` reconciliation found two "slim canonical" docs had grown to
6.6x / 5.7x their documented budgets because the snapshot-then-retrim cadence
(``documents/agent-lanes/docs-maintenance.md`` §Archive + Active-Work
Discipline) had stalled at W14. This gate fails loudly if a canonical regrows
past its hard ceiling, so the next bloat is caught in CI instead of by an audit.

Token estimate matches docs-maintenance.md: ``wc -w`` x 1.3.

Ceilings are a **regrowth ratchet** (at or above the aspirational budget in
docs-maintenance.md), not the budget itself:

- ``REFACTOR_OPTIMIZATION.md`` / ``REFACTOR_STATUS.md`` are genuine slim
  summaries — closed-phase detail lives in the dated ``archive/`` snapshots and
  the per-week ``active-work/W*.md`` trackers. They sit under their 2,500-token
  budget after the retrim; the ceiling adds headroom for the live tail.
- ``POST_POC_BACKLOG.md`` is the stable-ID **contract registry** plus the live
  open-item list; its size is contract/work driven, so its ceiling is set above
  the 3,000 "slim" target. When it approaches the ceiling, snapshot the closed
  acceptance bars to ``archive/backlog/`` and re-trim (do NOT drop stable IDs).
"""

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
