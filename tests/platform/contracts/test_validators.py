"""W8-5 unit tests: ``valid_extension_slug`` + ``ACTIVATION_REPORT_NAME_RE``.

The validator wraps ``MARKETPLACE_SLUG_TOKEN_RE`` (W8-2) so two surfaces
share one source-of-truth: marketplace identity helper and FastAPI
``Path(..., pattern=...)`` gate on ``workflows/activation_reports/router.py``.

Adversarial cases mirror the marketplace identity adversarial set so any
slug accepted by ``valid_extension_slug`` is also accepted by
``safe_marketplace_slug`` and vice versa.
"""

from __future__ import annotations

import pytest

from appcore.contracts.validators import (
    ACTIVATION_REPORT_NAME_RE,
    InvalidExtensionSlugError,
    valid_extension_slug,
)
from packages.marketplace_identity import MARKETPLACE_SLUG_TOKEN_RE


# ---------------------------------------------------------------------------
# Pattern source-of-truth invariants
# ---------------------------------------------------------------------------


def test_validator_uses_marketplace_slug_regex_constant() -> None:
    """The validator must defer to the W8-2 source-of-truth regex; if this
    test fails, the slug pattern has drifted between modules."""
    sample = "publisher.name-1.2.3"
    assert MARKETPLACE_SLUG_TOKEN_RE.fullmatch(sample) is not None
    assert valid_extension_slug(sample) == sample


def test_activation_report_name_regex_anchors_full_string() -> None:
    """The name pattern is anchored — partial matches must be rejected."""
    assert ACTIVATION_REPORT_NAME_RE.pattern.startswith("^")
    assert ACTIVATION_REPORT_NAME_RE.pattern.endswith("$")


def test_activation_report_name_regex_accepts_canonical_filename() -> None:
    name = "activation_report_publisher.name-1.2.3.json"
    assert ACTIVATION_REPORT_NAME_RE.fullmatch(name) is not None


# ---------------------------------------------------------------------------
# valid_extension_slug — happy path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    [
        "pub.ext-1.0.0",
        "ms-python.python-2024.0.1",
        "a",
        "publisher_token-with.dots-1.2.3",
        "Aa0",
    ],
)
def test_valid_extension_slug_accepts_well_formed_inputs(slug: str) -> None:
    assert valid_extension_slug(slug) == slug


# ---------------------------------------------------------------------------
# valid_extension_slug — adversarial reject
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    [
        "..",
        "../etc/passwd",
        "\\..\\bad",
        "with\x00null",
        ".leading-dot",
        "-leading-dash",
        "x" * 66,  # overlength: 66 chars total exceeds {0,64}+1 leading
        "pubр.name-1.0.0",  # noqa: RUF001, RUF003 — Cyrillic 'р' confusable test
        "pub.name; rm -rf /",
        "$(whoami)",
        "pub.name|cat",
        "",
    ],
)
def test_valid_extension_slug_rejects_adversarial_inputs(slug: str) -> None:
    """Per-token validator stays strict at 65 chars; the report-filename
    regex's wider bound applies only to the composed report-name body."""
    with pytest.raises(InvalidExtensionSlugError):
        valid_extension_slug(slug)


def test_valid_extension_slug_rejects_non_string_input() -> None:
    with pytest.raises(InvalidExtensionSlugError):
        valid_extension_slug(None)  # type: ignore[arg-type]


def test_invalid_extension_slug_error_is_value_error_subclass() -> None:
    assert issubclass(InvalidExtensionSlugError, ValueError)


# ---------------------------------------------------------------------------
# ACTIVATION_REPORT_NAME_RE — adversarial reject (the same set, sandwiched)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "..",
        "activation_report_../etc/passwd.json",
        "activation_report_\\..\\bad.json",
        "activation_report_\x00.json",
        ".activation_report_pub.name-1.0.0.json",
        "activation_report_-bad.json",
        "activation_report_"
        + "x" * 211
        + ".json",  # 211 chars body exceeds the 210-char producer ceiling
        "activation_report_pubр.name-1.0.json",  # noqa: RUF001, RUF003 — Cyrillic 'р' confusable test
        "activation_report.json",  # missing the underscore-prefixed slug
        "report_pub.name-1.0.0.json",  # missing activation_ prefix
        "activation_report_pub.name-1.0.0.txt",  # wrong suffix
        "activation_report_pub.name-1.0.0.json/",  # trailing slash
    ],
)
def test_activation_report_name_regex_rejects_adversarial(name: str) -> None:
    assert ACTIVATION_REPORT_NAME_RE.fullmatch(name) is None
