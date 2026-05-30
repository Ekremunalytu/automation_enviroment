"""ES-1b architecture gate (ADR 0016, Static Analysis Pre-Check): the
``rejected_static`` terminal status + ``static_report_path`` column landing.

ES-1b adds a seventh analysis-job status, ``rejected_static`` — the terminal
state a job enters when the static pre-check gate BLOCKs an extension before any
sandbox spin (ADR 0016 §Decision 1, block-and-warn). The correctness of the
landing rests on a few structural facts that are easy to break later, so they
are pinned here as module-level invariants:

1. ``rejected_static`` is a member of the canonical ``ANALYSIS_JOB_STATUSES``.
2. It is terminal, so it must NOT be in ``ACTIVE_ANALYSIS_JOB_STATUSES`` (a
   rejected job never holds the single-active slot).
3. The ``AnalysisJobStatus`` Literal mirrors the tuple exactly.
4. Because it is never active, the partial unique index
   ``uq_analysis_jobs_single_active`` keeps its
   ``('queued', 'running', 'cancelling')`` WHERE clause, and the ES-1b
   migration does NOT touch the index.
5. The ``static_report_path`` column is present (nullable) on the ORM model.

NOTE (landed at ES-3b): ``rejected_static`` is now a member of
``_TERMINAL_JOB_STATUSES``
(``appcore/storage/crud_ops/analysis_jobs/lifecycle.py``). The ES-3b orchestrator
wiring added it there together with the producer
(``crud.reject_analysis_job_static`` /
``job_service.reject_static_job``) and the ``analysis_service`` short-circuit.
The W13-3 invariant
``test_job_state_invariants.py::test_terminal_job_statuses_excludes_cancelling``
now pins the terminal set at the four terminal members (still excluding the
non-terminal ``cancelling``).
"""

from __future__ import annotations

from pathlib import Path
from typing import get_args

from appcore.contracts.schema_defs.analysis_jobs import (
    ACTIVE_ANALYSIS_JOB_STATUSES,
    ANALYSIS_JOB_STATUSES,
    AnalysisJobStatus,
)
from appcore.storage.model_defs.analysis_job import AnalysisJob

REPO_ROOT = Path(__file__).resolve().parents[2]
ORM_MODEL_PATH = REPO_ROOT / "appcore" / "storage" / "model_defs" / "analysis_job.py"
ES1B_MIGRATION_PATH = (
    REPO_ROOT
    / "alembic"
    / "versions"
    / "f4b9d2e7a1c3_add_static_report_path_to_analysis_jobs.py"
)

_REJECTED_STATIC = "rejected_static"
# The active partial-index WHERE clause as written in the ORM model. If a future
# change widened it to include rejected_static this exact substring would change.
_ACTIVE_INDEX_WHERE = (
    "postgresql_where=text(\"status IN ('queued', 'running', 'cancelling')\")"
)


def test_rejected_static_in_canonical_statuses() -> None:
    """ES-1b: rejected_static is a canonical analysis-job status."""
    assert _REJECTED_STATIC in ANALYSIS_JOB_STATUSES, (
        "rejected_static missing from ANALYSIS_JOB_STATUSES — the ES-1b "
        "terminal static-gate status must be a canonical member."
    )


def test_rejected_static_is_terminal_not_active() -> None:
    """ES-1b: rejected_static is terminal; it must never be in the active set."""
    assert _REJECTED_STATIC not in ACTIVE_ANALYSIS_JOB_STATUSES, (
        "rejected_static slipped into ACTIVE_ANALYSIS_JOB_STATUSES — a terminal "
        "rejection must not hold the single-active slot, and the partial unique "
        "index WHERE clause must stay in lockstep with the active set."
    )


def test_rejected_static_literal_mirrors_tuple() -> None:
    """ES-1b: the AnalysisJobStatus Literal mirrors the status tuple exactly."""
    assert set(get_args(AnalysisJobStatus)) == set(ANALYSIS_JOB_STATUSES), (
        "AnalysisJobStatus Literal drifted from ANALYSIS_JOB_STATUSES."
    )
    assert _REJECTED_STATIC in get_args(AnalysisJobStatus)


def test_partial_unique_index_unchanged_excludes_rejected_static() -> None:
    """ES-1b: rejected_static is terminal, so the active partial index is untouched."""
    orm_src = ORM_MODEL_PATH.read_text(encoding="utf-8")
    assert _ACTIVE_INDEX_WHERE in orm_src, (
        "uq_analysis_jobs_single_active WHERE clause changed — rejected_static "
        "is terminal and must NOT be added to the active partial unique index."
    )
    # The ES-1b migration adds only the column; it must not emit index DDL.
    # (Check for the operations, not the index name — the docstring names the
    # index precisely to explain why it is left untouched.)
    migration_src = ES1B_MIGRATION_PATH.read_text(encoding="utf-8")
    for ddl in (
        "op.create_index",
        "op.drop_index",
        "CREATE UNIQUE INDEX",
        "DROP INDEX",
    ):
        assert ddl not in migration_src, (
            f"the ES-1b migration must not touch the partial unique index "
            f"(found {ddl!r}) — rejected_static is terminal, the active set "
            f"is unchanged."
        )


def test_static_report_path_column_present() -> None:
    """ES-1b: the static_report_path column landed (nullable) on the ORM model."""
    columns = AnalysisJob.__table__.columns
    assert "static_report_path" in columns, (
        "static_report_path column missing from the AnalysisJob ORM model."
    )
    assert columns["static_report_path"].nullable is True, (
        "static_report_path must be nullable (pre-static / disabled-stage jobs)."
    )
