"""W15-1 behavioral regression: sync and async analyze surfaces must
return the same status code for the same exception class.

This pairs with the
``tests/architecture/test_analyze_error_taxonomy_parity.py`` arch gate
(structural invariant: tuples + helper coupling) by proving the
observable behavior — TestClient against the sync endpoint plus a unit
parametrize over the helper.

Codex 2026-05-10 audit M10 was: same request shape received different
status codes (sync 500 for ``TypeError``/``OSError``/``SQLAlchemyError``/
``ValueError``/``AttributeError``; async ``fail_job``). W15-1 closes
this by introducing ``ANALYZE_ERROR_TYPES`` and
:func:`analyze_error_to_http_response`; this test pins the mapping.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from executor.host import ExecutorError
from workflows.marketplace.analysis_errors import (
    ActivationReportLoadError,
    TriggerPlanError,
)
from workflows.marketplace.analysis_service import (
    ANALYZE_ERROR_TYPES,
    analyze_error_to_http_response,
)

ANALYZE_PAYLOAD = {
    "publisher": "ms-python",
    "name": "python",
    "version": "2025.0.0",
}


def _vsix_path_exists(exists: bool = True) -> MagicMock:
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    return mock_path


# ---------------------------------------------------------------------------
# Helper-level parametrize: every taxonomy class maps to the documented
# status code. Drift here would be caught by the arch gate as well, but
# this asserts the *observable status code*, not just the structural
# branch.
# ---------------------------------------------------------------------------

HELPER_CASES: tuple[tuple[Exception, int], ...] = (
    # ExecutorError → 502 via map_executor_error (with error_id contract).
    (ExecutorError("Install failed", returncode=1, output="err"), 502),
    # FileNotFoundError → 404 (missing prerequisite resource).
    (FileNotFoundError("VSIX file not found: ms-python.python-2025.0.0.vsix"), 404),
    # ActivationReportLoadError (ValueError subclass) → 502 (upstream-
    # report failure); must be matched BEFORE the generic ValueError
    # branch in the helper.
    (ActivationReportLoadError("activation_report_schema_invalid"), 502),
    # TriggerPlanError → 502 (planning-side closed-fail).
    (TriggerPlanError("trigger.planning.failed", "no matching trigger"), 502),
    # OSError → 502 (infra fault — file system, container, etc.).
    (OSError("disk write failed"), 502),
    # SQLAlchemyError → 502 (database fault).
    (SQLAlchemyError("db transaction aborted"), 502),
    # Generic ValueError (not a subclass of ActivationReportLoadError)
    # → 400 (client input problem).
    (ValueError("invalid manifest field"), 400),
    # TypeError → 500 (programming-class error surfaced explicitly).
    (TypeError("unsupported operand"), 500),
    # AttributeError → 500 (programming-class error).
    (AttributeError("missing attribute 'foo'"), 500),
)


@pytest.mark.parametrize(("exc", "expected_status"), HELPER_CASES)
def test_analyze_error_to_http_response_status_map(
    exc: Exception, expected_status: int
) -> None:
    """Each ``ANALYZE_ERROR_TYPES`` member maps to its documented status."""
    http_exc = analyze_error_to_http_response(exc)
    assert http_exc.status_code == expected_status, (
        f"{type(exc).__name__} → expected {expected_status}, "
        f"got {http_exc.status_code}; helper status map drift."
    )


def test_helper_rejects_unmapped_class() -> None:
    """Defensive: an exception class outside ``ANALYZE_ERROR_TYPES``
    must trip the helper's ``AssertionError`` rather than silently
    returning a default. The arch gate keeps the tuple and helper in
    sync, but the runtime fallback is an additional safety net.
    """

    class UnmappedError(RuntimeError):
        """Synthetic class outside the taxonomy."""

    with pytest.raises(AssertionError, match="Unmapped analyze error class"):
        analyze_error_to_http_response(UnmappedError("not in taxonomy"))


def test_taxonomy_classes_are_covered_by_helper_cases() -> None:
    """Vacuous-truth guard: every class in ``ANALYZE_ERROR_TYPES`` must
    appear at least once in ``HELPER_CASES``, otherwise the
    parametrized test could pass while a new taxonomy class lacks
    coverage. ``ActivationReportLoadError`` (a ``ValueError`` subclass
    inside the helper but not the tuple) is allowed as an extra.
    """
    covered = {type(exc) for exc, _ in HELPER_CASES}
    missing = set(ANALYZE_ERROR_TYPES) - covered
    assert not missing, (
        "HELPER_CASES does not cover every ANALYZE_ERROR_TYPES class: "
        f"missing {sorted(c.__name__ for c in missing)}. Add a case "
        "with the documented status before merging W15-1."
    )


# ---------------------------------------------------------------------------
# Endpoint-level parametrize: the sync ``POST /api/marketplace/analyze``
# returns the same status the helper maps to, proving the surface
# wire-up is consistent with the helper contract.
# ---------------------------------------------------------------------------


# Filter ExecutorError from the endpoint parametrize: its 502 detail body
# is asserted by the existing ``test_analyze_install_failure_502`` /
# ``test_analyze_automation_failure_502`` cases in test_router.py with
# the redaction contract; we don't re-prove that here. The remaining
# eight cases each map cleanly to ``str(exc)`` detail.
ENDPOINT_CASES: tuple[tuple[Exception, int], ...] = tuple(
    (exc, status)
    for exc, status in HELPER_CASES
    if not isinstance(exc, ExecutorError)
)


@pytest.mark.parametrize(("exc", "expected_status"), ENDPOINT_CASES)
def test_sync_analyze_endpoint_returns_helper_status_code(
    client: TestClient, exc: Exception, expected_status: int
) -> None:
    """POST /api/marketplace/analyze must return the helper-mapped status
    when ``execute_analysis_request`` raises an ``ANALYZE_ERROR_TYPES``
    member — proving the sync surface is wired through
    :func:`analyze_error_to_http_response` rather than the pre-W15-1
    open-coded four-clause except.
    """
    with (
        patch(
            "workflows.marketplace.analysis_service.marketplace_client.get_vsix_path",
            return_value=_vsix_path_exists(True),
        ),
        patch(
            "workflows.marketplace.router.execute_analysis_request",
            side_effect=exc,
        ),
    ):
        response = client.post("/api/marketplace/analyze", json=ANALYZE_PAYLOAD)

    assert response.status_code == expected_status, (
        f"{type(exc).__name__} → expected {expected_status} from sync "
        f"endpoint, got {response.status_code}. Response body: "
        f"{response.json()!r}"
    )
