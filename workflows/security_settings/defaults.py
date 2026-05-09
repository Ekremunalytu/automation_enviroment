"""Canonical key list, defaults, and sane validation bounds for the
operator-tunable VSIX hardening thresholds.

These values are the single source of truth for both the database seed
(applied on first read by ``service.load_vsix_thresholds``) and the
validation gate enforced by the PUT endpoint. The marketplace client
(``workflows/marketplace/client.py``) reads them at request time.
"""

from __future__ import annotations

from typing import Final, NamedTuple

# Canonical settings keys — must match the DB rows.
VSIX_MAX_UNCOMPRESSED_SIZE_KEY: Final[str] = "vsix_max_uncompressed_size"
VSIX_MAX_COMPRESSION_RATIO_KEY: Final[str] = "vsix_max_compression_ratio"
VSIX_MAX_FILE_COUNT_KEY: Final[str] = "vsix_max_file_count"

VSIX_THRESHOLD_KEYS: Final[tuple[str, ...]] = (
    VSIX_MAX_UNCOMPRESSED_SIZE_KEY,
    VSIX_MAX_COMPRESSION_RATIO_KEY,
    VSIX_MAX_FILE_COUNT_KEY,
)

# Defaults — match the W8-1 baseline + the 2026-05-08 entry-count raise
# (see workflows/marketplace/client.py rationale comment).
VSIX_THRESHOLD_DEFAULTS: Final[dict[str, int]] = {
    VSIX_MAX_UNCOMPRESSED_SIZE_KEY: 256 * 1024 * 1024,  # 256 MiB
    VSIX_MAX_COMPRESSION_RATIO_KEY: 100,
    VSIX_MAX_FILE_COUNT_KEY: 50_000,
}


class VsixThresholdBounds(NamedTuple):
    """Inclusive validation bounds for a single threshold setting."""

    min_value: int
    max_value: int


# Sane bounds — protect against an operator typo (zeroing a guard) or
# absurdly large values that would defeat the defense entirely.
THRESHOLD_BOUNDS: Final[dict[str, VsixThresholdBounds]] = {
    VSIX_MAX_UNCOMPRESSED_SIZE_KEY: VsixThresholdBounds(
        min_value=1 * 1024 * 1024,  # 1 MiB
        max_value=4 * 1024 * 1024 * 1024,  # 4 GiB
    ),
    VSIX_MAX_COMPRESSION_RATIO_KEY: VsixThresholdBounds(
        min_value=10,
        max_value=10_000,
    ),
    VSIX_MAX_FILE_COUNT_KEY: VsixThresholdBounds(
        min_value=100,
        max_value=1_000_000,
    ),
}


__all__ = [
    "THRESHOLD_BOUNDS",
    "VSIX_MAX_COMPRESSION_RATIO_KEY",
    "VSIX_MAX_FILE_COUNT_KEY",
    "VSIX_MAX_UNCOMPRESSED_SIZE_KEY",
    "VSIX_THRESHOLD_DEFAULTS",
    "VSIX_THRESHOLD_KEYS",
    "VsixThresholdBounds",
]
