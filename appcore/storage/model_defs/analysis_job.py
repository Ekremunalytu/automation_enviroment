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
