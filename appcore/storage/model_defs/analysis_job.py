"""Persisted metadata for marketplace analysis jobs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from appcore.storage.model_defs.base import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_boot_id: Mapped[str] = mapped_column(String, nullable=False)
    owner_pid: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    scenario: Mapped[str | None] = mapped_column(String, nullable=True)
    analysis_profile: Mapped[str | None] = mapped_column(String, nullable=True)
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    report_path: Mapped[str | None] = mapped_column(String, nullable=True)
    # ES-1b (ADR 0016, Static Analysis Pre-Check): path to the persisted
    # StaticAnalysisReport JSON (mirrors the `static_report_path` snapshot
    # field). Nullable — pre-static and disabled-stage jobs leave it NULL.
    static_report_path: Mapped[str | None] = mapped_column(String, nullable=True)
    install_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    automation_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    finished_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[float] = mapped_column(Float, nullable=False)
    # W13-3 (Codex H4): when `cancel_analysis_job` flips `running` to the new
    # non-terminal `cancelling` state, this column records when the drain was
    # signalled. Keeps the partial unique index honest — only one active row
    # (queued/running/cancelling) at any time.
    requested_cancel_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    # S2 (W23 B3, same-boot wedged-job recovery): the worker stamps this every
    # few seconds while a job is `running` (dedicated heartbeat thread). The
    # same-boot stale-running reaper compares ``now - COALESCE(last_heartbeat_at,
    # started_at)`` against the stale timeout to distinguish a hung/crashed
    # worker (which would otherwise hold the single-active slot forever) from a
    # slow phase, and fails it CLOSED without an API restart. Nullable: queued
    # rows have no worker yet, and pre-S2 / legacy rows leave it NULL (the reaper
    # falls back to ``started_at``). Operational-only — never flows through the
    # job snapshot Pydantic contracts; written via a targeted UPDATE and read
    # directly off the ORM by the reaper.
    last_heartbeat_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    # W26 / Stream 3 (B5 `[GOAL vsix-content-sha256-provenance]`): SHA-256 of the
    # analyzed .vsix archive (canonical 64-char lowercase), computed at
    # analyze-start and stamped on the row at creation via the create snapshot so
    # a completed job's verdict is provably bound to the bytes scanned. Two
    # byte-different same-version VSIX yield two distinct rows. Nullable: legacy
    # rows predate the column, and a row created before the hash is known (none
    # today — ``reserve_job`` receives it) leaves it NULL.
    vsix_sha256: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("ix_analysis_jobs_status", "status"),
        Index(
            "uq_analysis_jobs_single_active",
            text("(1)"),
            unique=True,
            postgresql_where=text("status IN ('queued', 'running', 'cancelling')"),
        ),
    )


__all__ = ["AnalysisJob"]
