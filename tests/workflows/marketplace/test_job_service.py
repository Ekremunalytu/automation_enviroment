"""Unit tests for marketplace job orchestration helpers."""

from __future__ import annotations

import pytest

from appcore.contracts.schemas import AnalyzeRequest
from appcore.contracts.validators import ACTIVATION_REPORT_NAME_RE
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


def test_build_report_name_output_matches_listing_regex_for_typical_input() -> None:
    """Producer/consumer drift gate: every name `build_report_name` writes
    must pass the listing/path-param filter; otherwise a completed analysis
    silently disappears from the activation-reports API surface."""
    request = AnalyzeRequest(
        publisher="ms-python",
        name="python",
        version="2026.5.2026042602",
    )
    name = job_service.build_report_name(request, "abcdef1234567890")
    assert ACTIVATION_REPORT_NAME_RE.fullmatch(name) is not None


def test_build_report_name_output_matches_listing_regex_at_maximum_slug_size() -> None:
    """Drift gate at the producer's worst case: each safe_marketplace_slug
    token is 65 chars (MARKETPLACE_SLUG_TOKEN_RE bound), so the longest
    name `build_report_name` can emit must still satisfy the regex."""
    max_token = "A" + "a" * 64  # 65 chars total, leading alphanumeric
    request = AnalyzeRequest(
        publisher=max_token,
        name=max_token,
        version=max_token,
    )
    name = job_service.build_report_name(request, "f" * 16)
    assert ACTIVATION_REPORT_NAME_RE.fullmatch(name) is not None
