"""Minimal ULID generation without external dependencies."""

from __future__ import annotations

import os
import time

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_LENGTH = 26
_TIMESTAMP_BITS = 48
_RANDOMNESS_BITS = 80


def generate_ulid() -> str:
    """Return a canonical 26-character ULID string."""

    timestamp_ms = time.time_ns() // 1_000_000
    if timestamp_ms >= 1 << _TIMESTAMP_BITS:
        msg = "ULID timestamp exceeds 48-bit range."
        raise ValueError(msg)

    randomness = int.from_bytes(os.urandom(_RANDOMNESS_BITS // 8), "big")
    value = (timestamp_ms << _RANDOMNESS_BITS) | randomness

    encoded: list[str] = ["0"] * _ULID_LENGTH
    for index in range(_ULID_LENGTH - 1, -1, -1):
        value, remainder = divmod(value, 32)
        encoded[index] = _CROCKFORD_BASE32[remainder]
    return "".join(encoded)


__all__ = ["generate_ulid"]
