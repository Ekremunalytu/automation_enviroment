"""Compatibility wrappers for marketplace analysis job persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.exc import OperationalError

from appcore.api.config import settings
from workflows.marketplace.job_service import (
    ActiveAnalysisJobError,
    build_report_name,
    create_job_snapshot,
    empty_job_steps,
    fail_job,
    get_active_persisted_job_snapshot,
    get_job_snapshot,
    get_persisted_job_snapshot,
    now,
    reserve_job,
    store_job,
    update_job,
    update_job_step,
)
from workflows.marketplace.job_service import (
    recover_interrupted_jobs as recover_interrupted_jobs_db,
)


def get_jobs_dir() -> Path:
    return Path(settings.project.OUTPUT_DIR) / "analysis_jobs"


def get_job_file(job_id: str) -> Path:
    return get_jobs_dir() / f"{job_id}.json"


def persist_job(job: dict[str, Any]) -> None:
    store_job(job)


def load_persisted_job(job_id: str) -> dict[str, Any]:
    return get_persisted_job_snapshot(job_id)


def get_active_job_snapshot() -> dict[str, Any] | None:
    return get_active_persisted_job_snapshot()


def recover_interrupted_jobs() -> int:
    try:
        return recover_interrupted_jobs_db()
    except OperationalError:
        return 0


def clear_job_cache() -> None:
    return None


__all__ = [
    "ActiveAnalysisJobError",
    "build_report_name",
    "clear_job_cache",
    "create_job_snapshot",
    "empty_job_steps",
    "fail_job",
    "get_active_job_snapshot",
    "get_job_file",
    "get_job_snapshot",
    "get_jobs_dir",
    "load_persisted_job",
    "now",
    "persist_job",
    "recover_interrupted_jobs",
    "reserve_job",
    "store_job",
    "update_job",
    "update_job_step",
]
