"""Internal schemas for persisted marketplace analysis jobs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ES-3b (ADR 0016, Static Analysis Pre-Check): the static pre-check gate runs
# BEFORE any sandbox spin, so its two steps lead the canonical order. When the
# `settings.static_analysis.ENABLED` flag is OFF (default until ES-5) the two
# static steps are seeded `skipped`; the dynamic stages are unchanged. Keep this
# tuple, the `AnalysisJobStepName` Literal, and `job_service.empty_job_steps`
# in lockstep — `_validate_steps` pins the exact 7-step order.
ANALYSIS_JOB_STEP_NAMES = (
    "static_analysis",
    "decision_gate",
    "reset_sandbox",
    "install_extension",
    "build_triggers",
    "run_monitoring",
    "finalize_report",
)
ANALYSIS_JOB_STEP_STATUSES = (
    "pending",
    "running",
    "completed",
    "skipped",
    "failed",
    "cancelled",
)
ANALYSIS_JOB_STATUSES = (
    "queued",
    "running",
    "cancelling",
    "completed",
    "failed",
    "cancelled",
    # ES-1b (ADR 0016, Static Analysis Pre-Check): terminal status set when the
    # static gate BLOCKs an extension before any sandbox spin (downstream steps
    # `skipped`). Terminal — deliberately NOT in ACTIVE_ANALYSIS_JOB_STATUSES
    # (it never holds the single-active slot, so the partial unique index WHERE
    # clause is unchanged). Its addition to `_TERMINAL_JOB_STATUSES` and the
    # producer/orchestrator wiring land together in ES-3b.
    "rejected_static",
)
# W13-3: `cancelling` is non-terminal (worker still drains shared executor /
# `/results/`); keeping it in the active set blocks `reserve_job` until the
# new `finalize_cancelled_analysis_job` helper transitions the row to the
# terminal `cancelled` state. Matches the partial unique index in
# `model_defs/analysis_job.py` and the `WHERE` clause in the Alembic
# revision `c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py`.
ACTIVE_ANALYSIS_JOB_STATUSES = ("queued", "running", "cancelling")

AnalysisJobStepName = Literal[
    "static_analysis",
    "decision_gate",
    "reset_sandbox",
    "install_extension",
    "build_triggers",
    "run_monitoring",
    "finalize_report",
]
AnalysisJobStepStatus = Literal[
    "pending",
    "running",
    "completed",
    "skipped",
    "failed",
    "cancelled",
]
AnalysisJobStatus = Literal[
    "queued",
    "running",
    "cancelling",
    "completed",
    "failed",
    "cancelled",
    # ES-1b: terminal static-gate rejection (see ANALYSIS_JOB_STATUSES note).
    "rejected_static",
]


class AnalysisJobStepProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: int = Field(ge=0)
    total: int = Field(ge=0)


class AnalysisJobStepRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: AnalysisJobStepName
    status: AnalysisJobStepStatus
    message: str = Field(min_length=1)
    error_code: str | None = None
    progress: AnalysisJobStepProgress | None = None


def _validate_steps(
    steps: list[AnalysisJobStepRecord],
) -> list[AnalysisJobStepRecord]:
    observed = [step.name for step in steps]
    expected = list(ANALYSIS_JOB_STEP_NAMES)
    if observed != expected:
        raise ValueError(
            "Analysis job steps must match the canonical step order: "
            + ", ".join(expected)
        )
    return steps


class AnalysisJobCreateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    owner_boot_id: str = Field(min_length=1)
    owner_pid: int = Field(ge=1)
    status: AnalysisJobStatus
    publisher: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    scenario: str | None = None
    analysis_profile: str | None = None
    current_step: AnalysisJobStepName | None = None
    message: str = Field(min_length=1)
    steps: list[AnalysisJobStepRecord]
    report_path: str | None = None
    # ES-1b (ADR 0016, Static Analysis Pre-Check): filesystem path to the
    # persisted StaticAnalysisReport JSON. Set when the static stage runs
    # (producer lands ES-3a/ES-3b); None for jobs without a static pre-check.
    static_report_path: str | None = None
    install_output: str | None = None
    automation_output: str | None = None
    error_detail: str | None = None
    error_code: str | None = None
    created_at: float = Field(ge=0)
    started_at: float | None = Field(default=None, ge=0)
    finished_at: float | None = Field(default=None, ge=0)
    updated_at: float = Field(ge=0)
    # W13-3: when a `running` job receives a cancel signal it transitions to
    # the non-terminal `cancelling` state and this column records when the
    # drain was requested. Stays `None` for jobs that complete normally.
    requested_cancel_at: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_steps(self) -> AnalysisJobCreateSnapshot:
        self.steps = _validate_steps(self.steps)
        return self


class AnalysisJobPersistedRecord(AnalysisJobCreateSnapshot):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class AnalysisJobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AnalysisJobStatus | None = None
    current_step: AnalysisJobStepName | None = None
    message: str | None = Field(default=None, min_length=1)
    report_path: str | None = None
    static_report_path: str | None = None
    install_output: str | None = None
    automation_output: str | None = None
    error_detail: str | None = None
    error_code: str | None = None
    started_at: float | None = Field(default=None, ge=0)
    finished_at: float | None = Field(default=None, ge=0)
    requested_cancel_at: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_has_changes(self) -> AnalysisJobUpdate:
        if not self.model_fields_set:
            raise ValueError("Analysis job updates must include at least one field.")
        return self


class AnalysisJobFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str = Field(min_length=1)
    error_code: str | None = None


class AnalysisJobStepUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_name: AnalysisJobStepName
    status: AnalysisJobStepStatus
    message: str = Field(min_length=1)
    error_code: str | None = None
    progress: AnalysisJobStepProgress | None = None


__all__ = [
    "ACTIVE_ANALYSIS_JOB_STATUSES",
    "ANALYSIS_JOB_STATUSES",
    "ANALYSIS_JOB_STEP_NAMES",
    "ANALYSIS_JOB_STEP_STATUSES",
    "AnalysisJobCreateSnapshot",
    "AnalysisJobFailure",
    "AnalysisJobPersistedRecord",
    "AnalysisJobStatus",
    "AnalysisJobStepName",
    "AnalysisJobStepProgress",
    "AnalysisJobStepRecord",
    "AnalysisJobStepStatus",
    "AnalysisJobStepUpdate",
    "AnalysisJobUpdate",
]
