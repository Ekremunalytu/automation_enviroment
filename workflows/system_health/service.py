"""Aggregate real appliance health and runtime inventory."""

from __future__ import annotations

import platform
import shutil
import socket
import sys
from datetime import UTC, datetime
from time import monotonic
from typing import Literal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import (
    SystemHealthResponse,
    SystemInventoryItem,
    SystemMetric,
    SystemServiceHealth,
)
from appcore.storage import crud
from executor.control import (
    ContainerRuntimeStatus,
    ExecutorControl,
    default_executor_control,
)
from executor.static_control import (
    StaticAnalyzerControl,
    default_static_analyzer_control,
)

_PROCESS_STARTED_AT = datetime.now(UTC)
_PROCESS_STARTED_MONOTONIC = monotonic()


def _format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    days, remainder = divmod(total, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _format_bytes(value: int) -> str:
    gib = value / (1024**3)
    return f"{gib:.1f} GiB"


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "No catalog writes yet"
    return value.astimezone(UTC).isoformat(timespec="seconds")


def _container_health(
    runtime: ContainerRuntimeStatus,
    *,
    service_id: str,
    name: str,
    detail: str,
) -> SystemServiceHealth:
    health: Literal["ok", "degraded", "down", "unknown"]
    if runtime.error:
        health = "unknown"
        status = "unavailable"
    elif runtime.running and runtime.health in {"healthy", "not-configured"}:
        health = "ok"
        status = runtime.health if runtime.health == "healthy" else "running"
    elif runtime.running:
        health = "degraded"
        status = runtime.health
    else:
        health = "down"
        status = runtime.status

    observations = [
        f"Container state: {runtime.status}",
        f"Health check: {runtime.health}",
    ]
    if runtime.started_at:
        observations.append(f"Started at: {runtime.started_at}")
    if runtime.oom_killed:
        observations.append("Docker reports an OOM kill")
    if runtime.error:
        observations.append(runtime.error)

    return SystemServiceHealth(
        id=service_id,
        name=name,
        health=health,
        status=status,
        detail=detail,
        source="Docker Engine · container state",
        metrics=[
            SystemMetric(label="container", value=runtime.container),
            SystemMetric(label="state", value=runtime.status),
            SystemMetric(label="health", value=runtime.health),
            SystemMetric(
                label="exit code",
                value="—" if runtime.exit_code is None else str(runtime.exit_code),
            ),
        ],
        observations=observations,
    )


def _catalog_health(db: Session) -> SystemServiceHealth:
    try:
        count, latest_write = crud.get_extension_inventory_summary(db)
        dialect = db.get_bind().dialect.name
    except SQLAlchemyError:
        return SystemServiceHealth(
            id="catalog",
            name="Catalog",
            health="down",
            status="database error",
            detail="Extension catalog could not be queried",
            source="PostgreSQL · extensions table",
            metrics=[
                SystemMetric(label="extensions", value="—"),
                SystemMetric(label="database", value="unavailable"),
                SystemMetric(label="latest write", value="—"),
            ],
            observations=["Catalog database query failed"],
        )

    latest = _format_timestamp(latest_write)
    return SystemServiceHealth(
        id="catalog",
        name="Catalog",
        health="ok",
        status="online",
        detail=f"{count:,} persisted extension record{'' if count == 1 else 's'}",
        source="PostgreSQL · extensions table",
        metrics=[
            SystemMetric(label="extensions", value=f"{count:,}"),
            SystemMetric(label="database", value=dialect),
            SystemMetric(label="latest write", value=latest),
        ],
        observations=[
            "Database query completed",
            f"Latest catalog write: {latest}",
        ],
    )


def build_system_health(
    db: Session,
    *,
    executor_control: ExecutorControl = default_executor_control,
    static_control: StaticAnalyzerControl = default_static_analyzer_control,
) -> SystemHealthResponse:
    """Build one partial-failure-tolerant appliance health snapshot."""

    observed_at = datetime.now(UTC)
    uptime = _format_duration(monotonic() - _PROCESS_STARTED_MONOTONIC)
    disk = shutil.disk_usage("/")
    api_status = settings.api.HEALTH_STATUS
    api_ok = api_status.casefold() in {"ok", "healthy", "ready", "up"}

    api_service = SystemServiceHealth(
        id="api",
        name="API",
        health="ok" if api_ok else "degraded",
        status=api_status,
        detail=f"{settings.project.NAME} · v{settings.project.VERSION}",
        source="/api/system/health · current process",
        metrics=[
            SystemMetric(label="status", value=api_status),
            SystemMetric(label="version", value=settings.project.VERSION),
            SystemMetric(label="uptime", value=uptime),
            SystemMetric(
                label="started",
                value=_PROCESS_STARTED_AT.isoformat(timespec="seconds"),
            ),
        ],
        observations=[
            "Aggregate health request served by the API process",
            f"Observed at: {observed_at.isoformat(timespec='seconds')}",
        ],
    )

    services = [
        api_service,
        _catalog_health(db),
        _container_health(
            executor_control.runtime_status(),
            service_id="sandbox",
            name="Sandbox",
            detail="Isolated dynamic-analysis executor",
        ),
        _container_health(
            static_control.runtime_status(),
            service_id="static",
            name="Static",
            detail="Network-isolated static pre-check",
        ),
    ]

    inventory = [
        SystemInventoryItem(label="hostname", value=socket.gethostname()),
        SystemInventoryItem(
            label="platform",
            value=f"{platform.system().lower()}/{platform.machine()}",
        ),
        SystemInventoryItem(label="kernel", value=platform.release()),
        SystemInventoryItem(
            label="python",
            value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ),
        SystemInventoryItem(
            label="disk used",
            value=f"{_format_bytes(disk.used)} / {_format_bytes(disk.total)}",
        ),
        SystemInventoryItem(
            label="observed",
            value=observed_at.isoformat(timespec="seconds"),
        ),
    ]

    return SystemHealthResponse(
        observed_at=observed_at,
        services=services,
        inventory=inventory,
    )


__all__ = ["build_system_health"]
