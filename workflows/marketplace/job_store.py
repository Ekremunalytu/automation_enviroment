"""Persistence and in-memory state for analysis jobs."""

from __future__ import annotations

import json
import os
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

from appcore.api.config import settings
from appcore.contracts.schemas import AnalyzeRequest

_JOB_LOCK = threading.Lock()
_ANALYSIS_JOBS: dict[str, dict[str, Any]] = {}
_ACTIVE_JOB_STATUSES = frozenset({"queued", "running"})
_PROCESS_BOOT_ID = uuid4().hex


def now() -> float:
    return time.time()


def get_jobs_dir() -> Path:
    return Path(settings.project.OUTPUT_DIR) / "analysis_jobs"


def get_job_file(job_id: str) -> Path:
    return get_jobs_dir() / f"{job_id}.json"


def persist_job(job: dict[str, Any]) -> None:
    jobs_dir = get_jobs_dir()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_file = get_job_file(job["job_id"])
    temp_file = job_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(job), encoding="utf-8")
    temp_file.replace(job_file)


def _is_active_job(job: dict[str, Any]) -> bool:
    return str(job.get("status")) in _ACTIVE_JOB_STATUSES


def _belongs_to_current_process(job: dict[str, Any]) -> bool:
    return job.get("owner_boot_id") == _PROCESS_BOOT_ID


def _interrupt_job(job: dict[str, Any], detail: str) -> dict[str, Any]:
    current_step = job.get("current_step")
    failed_index: int | None = None
    if current_step:
        for index, step in enumerate(job.get("steps", [])):
            if step.get("name") == current_step:
                step["status"] = "failed"
                step["message"] = detail
                failed_index = index
                break

    if failed_index is not None:
        current_step_name = str(current_step)
        for step in job["steps"][failed_index + 1 :]:
            if step.get("status") == "pending":
                step["status"] = "skipped"
                step["message"] = (
                    "Skipped because "
                    f"{current_step_name.replace('_', ' ')} was interrupted."
                )

    job.update(
        status="failed",
        message=detail,
        error_detail=detail,
        finished_at=now(),
        updated_at=now(),
    )
    return job


def _normalize_loaded_job(job: dict[str, Any]) -> dict[str, Any]:
    if _is_active_job(job) and not _belongs_to_current_process(job):
        _interrupt_job(
            job,
            "Analysis job was interrupted by an API restart. Start a new run.",
        )
        persist_job(job)
    return job


def load_persisted_job(job_id: str) -> dict[str, Any]:
    with open(get_job_file(job_id), encoding="utf-8") as handle:
        job = json.load(handle)
    if not isinstance(job, dict):
        raise KeyError(job_id)
    return _normalize_loaded_job(job)


def empty_job_steps() -> list[dict[str, str]]:
    return [
        {
            "name": "reset_sandbox",
            "status": "pending",
            "message": "Waiting for sandbox cleanup.",
        },
        {"name": "install_extension", "status": "pending", "message": "Queued."},
        {
            "name": "build_triggers",
            "status": "pending",
            "message": "Waiting for activation metadata.",
        },
        {
            "name": "run_monitoring",
            "status": "pending",
            "message": "Waiting for sandbox automation.",
        },
        {
            "name": "finalize_report",
            "status": "pending",
            "message": "Waiting for report export.",
        },
    ]


def build_report_name(request: AnalyzeRequest, run_id: str) -> str:
    return (
        f"activation_report_{request.publisher}.{request.name}-"
        f"{request.version}-{run_id[:12]}.json"
    )


def create_job_snapshot(request: AnalyzeRequest) -> dict[str, Any]:
    created_at = now()
    job_id = uuid4().hex
    return {
        "job_id": job_id,
        "owner_boot_id": _PROCESS_BOOT_ID,
        "owner_pid": os.getpid(),
        "status": "queued",
        "publisher": request.publisher,
        "name": request.name,
        "version": request.version,
        "scenario": request.scenario,
        "current_step": None,
        "message": "Queued for sandbox analysis.",
        "steps": empty_job_steps(),
        "report_path": build_report_name(request, job_id),
        "install_output": None,
        "automation_output": None,
        "error_detail": None,
        "created_at": created_at,
        "started_at": None,
        "finished_at": None,
        "updated_at": created_at,
    }


def store_job(job: dict[str, Any]) -> None:
    with _JOB_LOCK:
        _ANALYSIS_JOBS[job["job_id"]] = job
        persist_job(job)


def get_job_snapshot(job_id: str) -> dict[str, Any]:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is not None:
            return deepcopy(job)

    try:
        return load_persisted_job(job_id)
    except FileNotFoundError as exc:
        raise KeyError(job_id) from exc


def get_active_job_snapshot() -> dict[str, Any] | None:
    with _JOB_LOCK:
        for job in _ANALYSIS_JOBS.values():
            if _is_active_job(job):
                return deepcopy(job)

        jobs_dir = get_jobs_dir()
        if not jobs_dir.exists():
            return None

        for job_file in jobs_dir.glob("*.json"):
            try:
                job = load_persisted_job(job_file.stem)
            except (FileNotFoundError, KeyError, OSError, ValueError):
                continue

            if _is_active_job(job) and _belongs_to_current_process(job):
                _ANALYSIS_JOBS[job["job_id"]] = job
                return deepcopy(job)

    return None


def update_job(job_id: str, **updates: Any) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job
        job.update(updates)
        job["updated_at"] = now()
        persist_job(job)


def update_job_step(job_id: str, step_name: str, status: str, message: str) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job

        for step in job["steps"]:
            if step["name"] == step_name:
                step["status"] = status
                step["message"] = message
                break

        job["current_step"] = step_name if status == "running" else job["current_step"]
        if status in {"completed", "skipped"} and job["current_step"] == step_name:
            job["current_step"] = None
        if status == "failed":
            job["current_step"] = step_name

        job["updated_at"] = now()
        persist_job(job)


def fail_job(job_id: str, detail: str) -> None:
    with _JOB_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if job is None:
            job = load_persisted_job(job_id)
            _ANALYSIS_JOBS[job_id] = job

        current_step = job.get("current_step")
        failed_index: int | None = None
        if current_step:
            for index, step in enumerate(job["steps"]):
                if step["name"] == current_step:
                    step["status"] = "failed"
                    step["message"] = detail
                    failed_index = index
                    break

        if failed_index is not None:
            current_step_name = str(current_step)
            for step in job["steps"][failed_index + 1 :]:
                if step["status"] == "pending":
                    step["status"] = "skipped"
                    step["message"] = (
                        f"Skipped because {current_step_name.replace('_', ' ')} failed."
                    )

        job.update(
            status="failed",
            message=detail,
            error_detail=detail,
            finished_at=now(),
            updated_at=now(),
        )
        persist_job(job)


def clear_job_cache() -> None:
    with _JOB_LOCK:
        _ANALYSIS_JOBS.clear()


__all__ = [
    "_ANALYSIS_JOBS",
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
    "store_job",
    "update_job",
    "update_job_step",
]
