"""Measured appliance health aggregation tests."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from appcore.storage import crud
from executor.control import ExecutorControl
from executor.runtime_status import ContainerRuntimeStatus
from executor.static_control import StaticAnalyzerControl
from workflows.system_health.service import build_system_health


class _Dialect:
    name = "postgresql"


class _Bind:
    dialect = _Dialect()


class _Session:
    def get_bind(self) -> _Bind:
        return _Bind()


class _Control:
    def __init__(self, container: str, *, health: str = "healthy") -> None:
        self.container = container
        self.health = health

    def runtime_status(self) -> ContainerRuntimeStatus:
        return ContainerRuntimeStatus(
            container=self.container,
            status="running",
            health=self.health,
            running=True,
            started_at="2026-07-28T10:00:00Z",
            finished_at="",
            exit_code=0,
            oom_killed=False,
        )


def test_build_system_health_contains_only_measured_runtime_facts(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        crud,
        "get_extension_inventory_summary",
        lambda _db: (12, None),
    )

    response = build_system_health(
        cast(Session, _Session()),
        executor_control=cast(
            ExecutorControl,
            _Control("automation_executor"),
        ),
        static_control=cast(
            StaticAnalyzerControl,
            _Control("automation_static_analyzer", health="not-configured"),
        ),
    )

    assert [service.id for service in response.services] == [
        "api",
        "catalog",
        "sandbox",
        "static",
    ]
    assert all("mock" not in service.detail.casefold() for service in response.services)
    catalog = next(service for service in response.services if service.id == "catalog")
    assert catalog.status == "online"
    assert catalog.metrics[0].value == "12"
    static = next(service for service in response.services if service.id == "static")
    assert static.health == "ok"
    assert static.status == "running"
    assert response.inventory


def test_build_system_health_keeps_container_facts_when_catalog_query_fails(
    monkeypatch: Any,
) -> None:
    def fail_catalog(_db: Session) -> tuple[int, None]:
        raise SQLAlchemyError("database detail must not escape")

    monkeypatch.setattr(crud, "get_extension_inventory_summary", fail_catalog)

    response = build_system_health(
        cast(Session, _Session()),
        executor_control=cast(
            ExecutorControl,
            _Control("automation_executor"),
        ),
        static_control=cast(
            StaticAnalyzerControl,
            _Control("automation_static_analyzer"),
        ),
    )

    catalog = next(service for service in response.services if service.id == "catalog")
    sandbox = next(service for service in response.services if service.id == "sandbox")

    assert catalog.health == "down"
    assert catalog.status == "database error"
    assert "database detail" not in str(catalog)
    assert sandbox.health == "ok"
    assert sandbox.status == "healthy"
