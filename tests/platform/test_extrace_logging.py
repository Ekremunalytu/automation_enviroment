"""W14-5 sub-commit 1 — behavioral coverage for the
``appcore.logging`` factory + ``LogContextFilter``.

Pins the namespace taxonomy (factory rejects out-of-tree names),
the structured-field contract (``run_id`` / ``executor_fingerprint``
stamped on every record), and the idempotent install hook.

Run-ID stamping integration (env-source wiring) and executor
fingerprint provider integration land in W14-5 sub-commits 2 / 3
and grow this surface; this file covers the factory + filter
behavior in isolation so future regressions to the consolidation
layer surface here first.
"""

from __future__ import annotations

import logging

import pytest

from appcore.logging import (
    EXTRACE_LOGGER_ROOT,
    RUN_ID_ENV_VAR,
    LogContextFilter,
    LoggerNamespaceError,
    get_extrace_logger,
    install_extrace_log_context_filter,
    set_executor_fingerprint_provider,
)


def _make_record(name: str = "extrace.executor.test") -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="W14-5 test",
        args=(),
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# Namespace taxonomy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "extrace.executor.host",
        "extrace.executor.flows.playwright.monitor",
        "extrace.workflows.marketplace.client",
        "extrace.workflows.security_settings.router",
        "extrace.appcore.api.startup",
        "extrace.packages.analysis_engine.rules.a3",
    ],
)
def test_get_extrace_logger_accepts_approved_prefixes(name: str) -> None:
    logger = get_extrace_logger(name)
    assert isinstance(logger, logging.Logger)
    assert logger.name == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        "extrace",  # bare root is not enough — must include sub-namespace.
        "extrace.",  # trailing dot but no sub-area.
        "extrace.unknown.area",  # not in approved prefix list.
        "workflows.marketplace.client",  # legacy `__name__` pattern.
        "foo.bar.baz",
        "EXTRACE.executor.host",  # case-sensitive: uppercase rejected.
    ],
)
def test_get_extrace_logger_rejects_unapproved_names(name: str) -> None:
    with pytest.raises(LoggerNamespaceError):
        get_extrace_logger(name)


def test_get_extrace_logger_error_message_lists_approved_prefixes() -> None:
    """The rejection message must enumerate the approved prefixes so the
    caller can fix the namespace without reading the source."""
    with pytest.raises(LoggerNamespaceError) as exc_info:
        get_extrace_logger("foo.bar")
    message = str(exc_info.value)
    for prefix in (
        "extrace.executor.",
        "extrace.workflows.",
        "extrace.appcore.",
        "extrace.packages.",
    ):
        assert prefix in message


# ---------------------------------------------------------------------------
# Structured-field contract
# ---------------------------------------------------------------------------


def test_log_context_filter_returns_true_so_record_is_emitted() -> None:
    """The filter must never suppress records — it only annotates."""
    f = LogContextFilter()
    assert f.filter(_make_record()) is True


def test_log_context_filter_stamps_run_id_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-2026-05-13-abcdef")
    f = LogContextFilter()
    record = _make_record()
    f.filter(record)
    assert record.run_id == "epoch-2026-05-13-abcdef"


def test_log_context_filter_run_id_empty_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(RUN_ID_ENV_VAR, raising=False)
    f = LogContextFilter()
    record = _make_record()
    f.filter(record)
    assert record.run_id == ""


def test_log_context_filter_executor_fingerprint_empty_when_no_provider() -> None:
    set_executor_fingerprint_provider(None)
    try:
        f = LogContextFilter()
        record = _make_record()
        f.filter(record)
        assert record.executor_fingerprint == ""
    finally:
        set_executor_fingerprint_provider(None)


def test_log_context_filter_executor_fingerprint_calls_provider() -> None:
    set_executor_fingerprint_provider(lambda: "abcdef0")
    try:
        f = LogContextFilter()
        record = _make_record()
        f.filter(record)
        assert record.executor_fingerprint == "abcdef0"
    finally:
        set_executor_fingerprint_provider(None)


def test_log_context_filter_stamps_thread_name_default() -> None:
    f = LogContextFilter()
    record = _make_record()
    f.filter(record)
    assert isinstance(record.thread_name, str)
    assert record.thread_name  # non-empty.


def test_log_context_filter_preserves_explicit_thread_name() -> None:
    """If the caller already set ``thread_name`` (via ``extra=``), the
    filter must not overwrite it."""
    f = LogContextFilter()
    record = _make_record()
    record.thread_name = "explicit-override"
    f.filter(record)
    assert record.thread_name == "explicit-override"


# ---------------------------------------------------------------------------
# install_extrace_log_context_filter idempotency
# ---------------------------------------------------------------------------


@pytest.fixture()
def _reset_extrace_filters():
    extrace = logging.getLogger(EXTRACE_LOGGER_ROOT)
    original_filters = list(extrace.filters)
    extrace.filters = []
    try:
        yield extrace
    finally:
        extrace.filters = original_filters


def test_install_extrace_log_context_filter_attaches_filter(
    _reset_extrace_filters,
) -> None:
    install_extrace_log_context_filter()
    matched = [
        f for f in _reset_extrace_filters.filters if isinstance(f, LogContextFilter)
    ]
    assert len(matched) == 1


def test_install_extrace_log_context_filter_is_idempotent(
    _reset_extrace_filters,
) -> None:
    install_extrace_log_context_filter()
    install_extrace_log_context_filter()
    install_extrace_log_context_filter()
    matched = [
        f for f in _reset_extrace_filters.filters if isinstance(f, LogContextFilter)
    ]
    assert len(matched) == 1


def test_install_extrace_log_context_filter_propagates_to_children(
    _reset_extrace_filters, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A child logger under ``extrace.*`` must inherit the parent filter
    so emit-time the structured fields are stamped end-to-end."""
    install_extrace_log_context_filter()
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-child-propagation")

    child = get_extrace_logger("extrace.executor.host")
    record = _make_record(name=child.name)
    for filt in _reset_extrace_filters.filters:
        filt.filter(record)
    assert record.run_id == "epoch-child-propagation"
