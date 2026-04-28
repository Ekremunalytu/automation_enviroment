"""Unit tests for marketplace job orchestration helpers."""

from __future__ import annotations

import pytest

from appcore.contracts.schemas import AnalyzeRequest
from packages.marketplace_identity import MarketplaceIdentityError
from workflows.marketplace import job_service


def test_build_report_name_uses_safe_marketplace_slug() -> None:
    request = AnalyzeRequest(
        publisher="ms-python",
        name="python",
        version="2026.5.2026042602",
    )

    assert (
        job_service.build_report_name(request, "abcdef1234567890")
        == "activation_report_ms-python.python-2026.5.2026042602-abcdef123456.json"
    )


def test_build_report_name_rejects_adversarial_identity() -> None:
    request = AnalyzeRequest(
        publisher="../etc",
        name="python",
        version="2026.5.2026042602",
    )

    with pytest.raises(MarketplaceIdentityError):
        job_service.build_report_name(request, "abcdef1234567890")
