"""Marketplace workflow test defaults."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def enable_dynamic_analysis_for_existing_marketplace_tests() -> Generator[None]:
    """Preserve full-pipeline test intent; dedicated tests pin static-only mode."""
    with patch(
        "workflows.marketplace.router.load_dynamic_analysis_enabled",
        return_value=True,
    ):
        yield
