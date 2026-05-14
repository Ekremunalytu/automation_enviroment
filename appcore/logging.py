"""Central logger factory + structured-field context filter for the
``extrace.*`` namespace (W14-5 §11.10 GOAL: logger consolidation).

Every logger used in production code under ``executor/``, ``workflows/``,
``appcore/`` (and any future ``packages/`` consumer) must come from
:func:`get_extrace_logger`. The factory enforces the ``extrace.<area>.*``
naming taxonomy so emit lines stay greppable across worker threads,
docker exec boundaries, and the daemon thread orchestration. The
:class:`LogContextFilter` stamps each :class:`logging.LogRecord` with
the ``EXTRACE_EPOCH_RUN_ID`` env var (W14-5 sub-commit 2 wiring) plus
the executor runtime fingerprint (W14-5 sub-commit 3 wiring) so a
single scan run produces a correlatable log stream end-to-end.

Direct ``logging.getLogger(...)`` calls inside the scanned subtrees are
forbidden by the W14-5 architecture gate
(``tests/architecture/test_logger_consolidation.py``); the factory is
the single chokepoint that guarantees the structured-field contract
holds on every emit.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import Final

EXTRACE_LOGGER_ROOT: Final[str] = "extrace"
_APPROVED_PREFIXES: Final[tuple[str, ...]] = (
    "extrace.executor.",
    "extrace.workflows.",
    "extrace.appcore.",
    "extrace.packages.",
)
RUN_ID_ENV_VAR: Final[str] = "EXTRACE_EPOCH_RUN_ID"

_fingerprint_provider: Callable[[], str] | None = None


class LoggerNamespaceError(ValueError):
    """Raised when a logger is requested outside the approved extrace namespace."""


def get_extrace_logger(name: str) -> logging.Logger:
    """Return a logger under the ``extrace.*`` namespace.

    The provided ``name`` must start with one of the approved area
    prefixes: ``extrace.executor.``, ``extrace.workflows.``,
    ``extrace.appcore.``, or ``extrace.packages.``. The factory is the
    single chokepoint enforced by
    ``tests/architecture/test_logger_consolidation.py`` so the
    structured-field contract (run_id, executor_fingerprint) holds on
    every record without the caller having to wire it up.
    """
    if not name.startswith(_APPROVED_PREFIXES):
        raise LoggerNamespaceError(
            f"logger name {name!r} must start with one of "
            f"{', '.join(_APPROVED_PREFIXES)}; use a dotted area "
            "prefix so the W14-5 consolidation invariant holds."
        )
    return logging.getLogger(name)


def _stamp_record(record: logging.LogRecord) -> None:
    """Apply the W14-5 structured-field contract to ``record``.

    - ``record.run_id`` — value of ``EXTRACE_EPOCH_RUN_ID`` at emit
      time, or the empty string when the env var is unset.
    - ``record.executor_fingerprint`` — short fingerprint string
      supplied by the registered provider (W14-5 sub-commit 3 wires
      ``executor.runtime_fingerprint.executor_fingerprint``); empty
      string when no provider is registered.
    - ``record.thread_name`` — current thread name (only added when
      not already present, so explicit ``extra={"thread_name": ...}``
      overrides win).
    """
    record.run_id = os.environ.get(RUN_ID_ENV_VAR, "")
    provider = _fingerprint_provider
    record.executor_fingerprint = provider() if provider is not None else ""
    if not hasattr(record, "thread_name"):
        record.thread_name = threading.current_thread().name


class LogContextFilter(logging.Filter):
    """Standalone filter form of the W14-5 structured-field contract.

    Use this form to stamp records on a specific handler when the
    global ``LogRecord`` factory installed by
    :func:`install_extrace_log_context_filter` is not in scope (e.g.
    inside isolated tests, or when a third-party logging integration
    has already overridden the factory). In production code the
    global factory is the preferred path — it stamps every record at
    creation time, before any handler / filter runs, so child loggers
    inherit the contract automatically (the standard ``logging``
    framework does not propagate filters from parent loggers to
    children during ``callHandlers``).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        _stamp_record(record)
        return True


def _make_extrace_log_record_factory(base_factory):
    """Wrap ``base_factory`` so every produced ``LogRecord`` is stamped
    with the W14-5 structured-field contract before it is returned."""

    def _extrace_factory(*args, **kwargs) -> logging.LogRecord:
        record = base_factory(*args, **kwargs)
        _stamp_record(record)
        return record

    _extrace_factory._is_extrace_factory = True  # type: ignore[attr-defined]
    return _extrace_factory


def install_extrace_log_context_filter() -> None:
    """Install the W14-5 ``LogRecord`` factory so every record carries
    the structured-field contract.

    Idempotent: subsequent calls no-op if the factory is already in
    place (the wrapper carries an ``_is_extrace_factory`` sentinel).
    Call from executor entry points and the FastAPI startup hook so
    every emit under the ``extrace.*`` namespace inherits the run-ID
    and fingerprint stamping without per-call wiring.

    The function name preserves W14-5 sub-commit 1's API contract;
    sub-commit 2 retargets the implementation from a parent-logger
    filter (which the Python ``logging`` framework does not propagate
    to child loggers during ``callHandlers``) to a global
    ``LogRecord`` factory — the only emit-time chokepoint that
    actually catches every record.
    """
    current = logging.getLogRecordFactory()
    if getattr(current, "_is_extrace_factory", False):
        return
    logging.setLogRecordFactory(_make_extrace_log_record_factory(current))


def set_executor_fingerprint_provider(provider: Callable[[], str] | None) -> None:
    """W14-5 sub-commit 3 hook.

    Register the executor runtime fingerprint provider that
    :class:`LogContextFilter` invokes once per record. Pass ``None`` to
    reset (test-only). The provider must always return a string —
    raising would corrupt log emission and is treated as a contract
    violation by the test surface.
    """
    global _fingerprint_provider
    _fingerprint_provider = provider


__all__ = [
    "EXTRACE_LOGGER_ROOT",
    "RUN_ID_ENV_VAR",
    "LogContextFilter",
    "LoggerNamespaceError",
    "get_extrace_logger",
    "install_extrace_log_context_filter",
    "set_executor_fingerprint_provider",
]
