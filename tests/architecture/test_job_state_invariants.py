"""W13-3 architecture gate: analysis-job state-machine invariants.

Codex H4 (`reserve_job` released the single-active lock the moment a
cancel signal landed, allowing a second job over the shared executor
while the worker thread was still draining) is closed by introducing a
non-terminal `cancelling` state between `running` and `cancelled`. The
correctness of the fix depends on a small set of structural invariants
that are easy to break by accident — promote `cancelling` to a terminal,
drop it from the active set, or forget to update the partial unique
index in the next Alembic revision — and any one of those would
silently reopen the race. This gate pins the four invariants as
module-level facts so a regression flips a tests/architecture failure
instead of a quiet runtime crash.

Asserted invariants:

1. ``_TERMINAL_JOB_STATUSES`` (in
   ``appcore/storage/crud_ops/analysis_jobs/lifecycle.py``) is exactly
   ``frozenset({"completed", "failed", "cancelled"})`` — adding
   ``cancelling`` here lets ``reserve_job`` admit a second job during
   the drain and reopens Codex H4.

2. ``ACTIVE_ANALYSIS_JOB_STATUSES`` (in
   ``appcore/contracts/schema_defs/analysis_jobs.py``) contains
   ``"cancelling"`` — removing it lets ``get_active_analysis_job`` return
   None during the drain, with the same effect.

3. ``ANALYSIS_JOB_STATUSES`` (same module) is the 7-tuple
   ``("queued", "running", "cancelling", "completed", "failed",
   "cancelled", "rejected_static")`` — keeps the tuple/literal/migration
   triple in sync. ``rejected_static`` is the ES-1b / ADR 0016 terminal
   static-gate rejection (terminal, never active; pinned by
   ``tests/architecture/test_rejected_static_terminal_status.py``).

4. The Alembic revision
   ``c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py`` keeps the
   partial unique index WHERE clause aligned with
   ``ACTIVE_ANALYSIS_JOB_STATUSES`` — without the literal in the upgrade
   body the DB-level lock would still admit cancelling rows.

Defense-in-depth siblings:

- ``tests/architecture/test_cancel_poll_points.py`` (W13-3 wiring gate
  — 5 cancel-poll points in execute_analysis_request).
- ``tests/platform/storage/test_analysis_jobs_lifecycle.py`` (W13-3 CRUD
  regressions for the two-phase cancel contract).
"""

from __future__ import annotations

from pathlib import Path

from appcore.contracts.schema_defs.analysis_jobs import (
    ACTIVE_ANALYSIS_JOB_STATUSES,
    ANALYSIS_JOB_STATUSES,
)
from appcore.storage.crud_ops.analysis_jobs.lifecycle import _TERMINAL_JOB_STATUSES

REPO_ROOT = Path(__file__).resolve().parents[2]
W13_3_MIGRATION_PATH = (
    REPO_ROOT
    / "alembic"
    / "versions"
    / "c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py"
)


def test_terminal_job_statuses_excludes_cancelling() -> None:
    """W13-3: cancelling is non-terminal; promoting it would reopen H4."""
    assert frozenset({"completed", "failed", "cancelled"}) == _TERMINAL_JOB_STATUSES, (
        "_TERMINAL_JOB_STATUSES drift detected — Codex H4 invariant: "
        "cancelling must NOT be in the terminal set, otherwise "
        "reserve_job releases the lock during the drain and a second "
        "job lands on the shared executor."
    )
    assert "cancelling" not in _TERMINAL_JOB_STATUSES, (
        "cancelling slipped into _TERMINAL_JOB_STATUSES — reopens H4."
    )


def test_active_job_statuses_includes_cancelling() -> None:
    """W13-3: cancelling rows hold the single-active slot for reserve_job."""
    assert "cancelling" in ACTIVE_ANALYSIS_JOB_STATUSES, (
        "ACTIVE_ANALYSIS_JOB_STATUSES dropped 'cancelling' — "
        "get_active_analysis_job returns None during drain, "
        "ActiveAnalysisJobError stops being raised, and Codex H4 "
        "reopens at the workflow layer."
    )
    # The other two members are the original queued/running pre-W13-3
    # set; pinning them here catches accidental shrinkage.
    assert set(ACTIVE_ANALYSIS_JOB_STATUSES) == {"queued", "running", "cancelling"}, (
        f"ACTIVE_ANALYSIS_JOB_STATUSES unexpected membership "
        f"{ACTIVE_ANALYSIS_JOB_STATUSES!r} — the partial unique index "
        f"WHERE clause must stay in lockstep with this tuple."
    )


def test_analysis_job_statuses_tuple_matches_canonical_seven() -> None:
    """ES-1b: the 7-status tuple has to match the Pydantic literal and migration."""
    assert set(ANALYSIS_JOB_STATUSES) == {
        "queued",
        "running",
        "cancelling",
        "completed",
        "failed",
        "cancelled",
        "rejected_static",
    }, (
        f"ANALYSIS_JOB_STATUSES drift {ANALYSIS_JOB_STATUSES!r} — "
        f"keep the tuple in lockstep with AnalysisJobStatus Literal "
        f"and the Alembic partial-index WHERE clause."
    )
    assert len(ANALYSIS_JOB_STATUSES) == 7, (
        f"ANALYSIS_JOB_STATUSES must be 7 members, got {len(ANALYSIS_JOB_STATUSES)}."
    )


def test_alembic_migration_partial_index_includes_cancelling() -> None:
    """W13-3: the Alembic upgrade body must extend the WHERE to cancelling.

    Reading the migration as plain text rather than parsing the AST keeps
    the gate robust against minor formatting churn (Python f-strings,
    whitespace) while still pinning the meaningful literal.
    """
    assert W13_3_MIGRATION_PATH.exists(), (
        f"{W13_3_MIGRATION_PATH.relative_to(REPO_ROOT)} missing — the "
        "W13-3 schema migration is the canonical evidence that the "
        "DB-level partial unique index covers `cancelling`."
    )
    text = W13_3_MIGRATION_PATH.read_text(encoding="utf-8")
    expected_clause = "WHERE status IN ('queued', 'running', 'cancelling')"
    assert expected_clause in text, (
        f"{W13_3_MIGRATION_PATH.relative_to(REPO_ROOT)}: upgrade body must "
        f"contain the literal {expected_clause!r} so the partial unique "
        f"index keeps blocking reserve_job while a cancelling row exists."
    )
    # The downgrade has to be careful to NOT carry `cancelling` in the
    # rebuilt index — otherwise a rollback would leave an inconsistent
    # schema. Pin the absence as a structural fact.
    assert "WHERE status IN ('queued', 'running')" in text, (
        f"{W13_3_MIGRATION_PATH.relative_to(REPO_ROOT)}: downgrade body "
        f"must rebuild the pre-W13-3 partial unique index "
        f"(WHERE status IN ('queued', 'running'))."
    )
