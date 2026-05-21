"""W14-5 sub-commit 2 — end-to-end run-ID stamping integration coverage.

Pins the actual emit pipeline: a ``get_extrace_logger(...)`` logger's
``warning()`` reaches a captured handler with ``record.run_id``
stamped from ``EXTRACE_EPOCH_RUN_ID``. The sub-commit 1 factory test
exercises the filter in isolation; this file exercises the wired-up
chain (parent ``extrace`` logger filter + child logger emit + handler
receives the stamped record) so a regression in either the install
hook or the filter propagation surfaces here first.

Also pins value freshness: the filter reads the env var per-record,
not per-process — so an in-flight env change between two emits
produces two distinct ``run_id`` values on the records.
"""

from __future__ import annotations

import logging

import pytest

from appcore.logging import (
    EXTRACE_LOGGER_ROOT,
    RUN_ID_ENV_VAR,
    get_extrace_logger,
    install_extrace_log_context_filter,
)


class _CaptureHandler(logging.Handler):
    """In-memory log handler that retains every LogRecord it processes
    so the test can inspect the structured fields stamped by the
    W14-5 filter."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture()
def _wired_extrace_chain():
    """Install the W14-5 LogRecord factory + attach a capture handler
    to the ``extrace`` parent logger so emit by any child logger
    propagates up and is recorded with structured fields stamped.

    Snapshot/restore the factory and handler list so the fixture
    does not leak state into sibling tests in the same pytest
    session.
    """
    extrace = logging.getLogger(EXTRACE_LOGGER_ROOT)
    original_factory = logging.getLogRecordFactory()
    original_handlers = list(extrace.handlers)
    original_level = extrace.level
    extrace.handlers = []
    extrace.setLevel(logging.DEBUG)

    handler = _CaptureHandler()
    extrace.addHandler(handler)
    install_extrace_log_context_filter()

    try:
        yield handler
    finally:
        logging.setLogRecordFactory(original_factory)
        extrace.handlers = original_handlers
        extrace.setLevel(original_level)


# ---------------------------------------------------------------------------
# End-to-end emit pipeline
# ---------------------------------------------------------------------------


def test_factory_logger_emit_carries_run_id_via_parent_filter(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-end-to-end-abcdef")

    logger = get_extrace_logger("extrace.executor.host")
    logger.warning("W14-5 emit through the full chain")

    assert _wired_extrace_chain.records
    record = _wired_extrace_chain.records[-1]
    assert record.run_id == "epoch-end-to-end-abcdef"


def test_run_id_propagates_to_deep_child_logger_emit(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deep child names (``extrace.executor.flows.playwright.monitor.runtime``)
    must inherit the filter via the standard Python logging hierarchy."""
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-deep-child")

    deep = get_extrace_logger("extrace.executor.flows.playwright.monitor.runtime")
    deep.warning("deep emit")

    assert _wired_extrace_chain.records[-1].run_id == "epoch-deep-child"


def test_run_id_updates_per_record_when_env_changes(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The filter reads the env var on every record, not once at
    install time. An in-flight change (e.g. a new scan's epoch boot)
    must be reflected on subsequent emits."""
    logger = get_extrace_logger("extrace.executor.host")

    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-first")
    logger.warning("first emit")

    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-second")
    logger.warning("second emit")

    first, second = _wired_extrace_chain.records[-2:]
    assert first.run_id == "epoch-first"
    assert second.run_id == "epoch-second"


def test_run_id_empty_when_env_unset_for_record(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(RUN_ID_ENV_VAR, raising=False)

    logger = get_extrace_logger("extrace.workflows.marketplace.client")
    logger.warning("no run id")

    assert _wired_extrace_chain.records[-1].run_id == ""


def test_log_context_filter_does_not_drop_records(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The filter contract is *stamp-only* — never suppress. Multiple
    emits in a row must all reach the handler regardless of env state."""
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-no-drop")
    logger = get_extrace_logger("extrace.executor.host")

    logger.warning("one")
    logger.warning("two")
    logger.warning("three")

    assert len(_wired_extrace_chain.records) == 3
    assert [r.run_id for r in _wired_extrace_chain.records] == [
        "epoch-no-drop",
        "epoch-no-drop",
        "epoch-no-drop",
    ]


def test_filter_stamps_record_regardless_of_log_level(
    _wired_extrace_chain: _CaptureHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``INFO`` / ``DEBUG`` / ``ERROR`` records that survive the level
    threshold must each receive the run-ID stamp."""
    monkeypatch.setenv(RUN_ID_ENV_VAR, "epoch-multi-level")
    logger = get_extrace_logger("extrace.executor.host")

    logger.debug("debug emit")
    logger.info("info emit")
    logger.warning("warning emit")
    logger.error("error emit")

    assert all(r.run_id == "epoch-multi-level" for r in _wired_extrace_chain.records)


# ---------------------------------------------------------------------------
# main.py startup hook regression
# ---------------------------------------------------------------------------


def test_create_app_installs_extrace_log_record_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI ``create_app`` factory must install the LogRecord
    factory wrapper early so every API-side emit carries the W14-5
    structured-field contract. Without this hook the gate above
    passes in isolation but production emit drops the run-ID.

    Regression idiom: reset the factory, invoke ``create_app``, then
    assert the factory carries the W14-5 ``_is_extrace_factory``
    sentinel. ``EXTRACE_SKIP_JOB_RECOVERY=1`` short-circuits the DB
    recovery path inside ``create_app`` so the test does not need a
    live database for the install hook regression check.
    """
    monkeypatch.setenv("EXTRACE_SKIP_JOB_RECOVERY", "1")
    original_factory = logging.getLogRecordFactory()
    logging.setLogRecordFactory(logging.LogRecord)
    try:
        import importlib

        import main

        importlib.reload(main)
        main.create_app(recover_jobs=False)
        installed = logging.getLogRecordFactory()
        assert getattr(installed, "_is_extrace_factory", False) is True, (
            "create_app() must call install_extrace_log_context_filter() "
            "exactly once (idempotent install). W14-5 sub-commit 2 wires "
            "this; if the call is removed, run-ID stamping silently "
            "stops in production while sub-commit 1 unit tests stay green."
        )
    finally:
        logging.setLogRecordFactory(original_factory)
