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


def _env_bool(name: str, default: bool) -> bool:
    raw = _env_value(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
class StaticAnalyzerSettings:
    """Hardened static-analyzer container handles (ES-2, ADR 0016).

    Mirrors the executor-side container knobs so ``executor/static_host.py``
    can drive ``automation_static_analyzer`` via ``docker exec`` the same way
    ``host.py`` drives the executor.
    """

    CONTAINER_NAME: str
    DOCKER_EXEC_TIMEOUT: int
    ENTRYPOINT_MODULE: str


@dataclass(frozen=True, slots=True)
class StaticAnalysisSettings:
    """Static pre-check stage feature flag + budget (ES-2, ADR 0016).

    ``ENABLED`` is ON by default from the ES-5 close-out, which flipped it after
    smoke evidence passed (ADR 0016 §Operational notes).

    ES-5 (``static-settings-timeout-naming``): the budget field is named
    ``TIMEOUT_BUDGET_S`` (env ``STATIC_ANALYSIS_TIMEOUT_BUDGET_S``) to match the
    app-side ``appcore.api.config.StaticAnalysisSettings`` — one logical timeout,
    one env key across both mirrors.
    """

    ENABLED: bool
    TIMEOUT_BUDGET_S: int


@dataclass(frozen=True, slots=True)
class Settings:
    project: ProjectSettings
    executor: ExecutorSettings
    static_analyzer: StaticAnalyzerSettings
    static_analysis: StaticAnalysisSettings


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
        static_analyzer=StaticAnalyzerSettings(
            CONTAINER_NAME=_env_str(
                "STATIC_ANALYZER_CONTAINER_NAME", "automation_static_analyzer"
            ),
            DOCKER_EXEC_TIMEOUT=_env_int("STATIC_ANALYZER_DOCKER_EXEC_TIMEOUT", 60),
            ENTRYPOINT_MODULE=_env_str(
                "STATIC_ANALYZER_ENTRYPOINT_MODULE", "static_runtime"
            ),
        ),
        static_analysis=StaticAnalysisSettings(
            ENABLED=_env_bool("STATIC_ANALYSIS_ENABLED", True),
            TIMEOUT_BUDGET_S=_env_int("STATIC_ANALYSIS_TIMEOUT_BUDGET_S", 30),
        ),
    )


settings = build_settings()
