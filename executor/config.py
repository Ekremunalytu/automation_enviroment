"""Executor-local configuration surface.

This module mirrors the small subset of project settings that executor-facing
host helpers need, without importing runtime appcore modules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values

_ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


@lru_cache(maxsize=1)
def _dotenv_values() -> dict[str, str]:
    if not _ENV_FILE_PATH.exists():
        return {}
    return {
        key: value
        for key, value in dotenv_values(_ENV_FILE_PATH).items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is not None:
        return value
    return _dotenv_values().get(name)


def _env_str(name: str, default: str) -> str:
    value = _env_value(name)
    if value is None:
        return default
    return value


def _env_int(name: str, default: int) -> int:
    raw = _env_value(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    EXTENSION_DIR: str
    OUTPUT_DIR: str


@dataclass(frozen=True, slots=True)
class ExecutorSettings:
    CONTAINER_NAME: str
    EXTENSIONS_CONTAINER_PATH: str
    PLAYWRIGHT_FLOW_DIR: str
    ENTRYPOINT_MODULE: str
    RELOAD_SCRIPT_MODULE: str
    RESET_SCRIPT_MODULE: str
    DOCKER_EXEC_TIMEOUT: int


@dataclass(frozen=True, slots=True)
class Settings:
    project: ProjectSettings
    executor: ExecutorSettings


def build_settings() -> Settings:
    return Settings(
        project=ProjectSettings(
            EXTENSION_DIR=_env_str("PROJECT_EXTENSION_DIR", "extensions"),
            OUTPUT_DIR=_env_str("PROJECT_OUTPUT_DIR", "output"),
        ),
        executor=ExecutorSettings(
            CONTAINER_NAME=_env_str("EXECUTOR_CONTAINER_NAME", "automation_executor"),
            EXTENSIONS_CONTAINER_PATH=_env_str(
                "EXECUTOR_EXTENSIONS_CONTAINER_PATH",
                "/extensions-input",
            ),
            PLAYWRIGHT_FLOW_DIR=_env_str(
                "EXECUTOR_PLAYWRIGHT_FLOW_DIR",
                "/home/executor/flows/playwright",
            ),
            ENTRYPOINT_MODULE=_env_str(
                "EXECUTOR_ENTRYPOINT_MODULE",
                "executor.flows.playwright.entrypoint",
            ),
            RELOAD_SCRIPT_MODULE=_env_str(
                "EXECUTOR_RELOAD_SCRIPT_MODULE",
                "executor.flows.playwright.reload_vscode",
            ),
            RESET_SCRIPT_MODULE=_env_str(
                "EXECUTOR_RESET_SCRIPT_MODULE",
                "executor.flows.playwright.reset_state",
            ),
            DOCKER_EXEC_TIMEOUT=_env_int("EXECUTOR_DOCKER_EXEC_TIMEOUT", 300),
        ),
    )


settings = build_settings()
