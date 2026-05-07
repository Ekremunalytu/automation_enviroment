"""ContentSample evidence artifact with secret redaction (W8-6).

Rule matches occasionally embed extension-controlled raw text (``.env``
lines, log fragments, header dumps) into evidence artifacts that get
serialised to disk. Without filtering, those snippets can leak AWS
keys, bearer tokens, private-key bodies, generic API keys, or DB
connection strings. ``ContentSample`` is the single carrier for such
snippets; its ``value`` field is filtered through ``redact_secrets``
on construction *and* on every assignment so consumers cannot read or
persist the raw secret form.

See ADR 0003 §6.1 for the secret-class taxonomy and policy bar.
"""

from __future__ import annotations

import re
from typing import Annotated, Final, Literal

from pydantic import ConfigDict, Field, field_validator

from packages.analysis_contracts.contracts import StrictContractModel

SECRET_CLASSES: Final[frozenset[str]] = frozenset(
    {"aws", "bearer", "private_key", "api_key", "db_url"}
)

_REDACTION_PATTERNS: Final[tuple[tuple[str, re.Pattern[str], str], ...]] = (
    (
        "aws",
        re.compile(
            r"(AWS_(?:SECRET_ACCESS_KEY|ACCESS_KEY_ID)\s*[:=]\s*)"
            r"[A-Za-z0-9/+=]{16,}",
        ),
        r"\1[REDACTED:aws]",
    ),
    (
        "aws",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "[REDACTED:aws]",
    ),
    (
        "bearer",
        re.compile(
            r"(Authorization\s*:\s*)Bearer\s+[A-Za-z0-9._\-+/=]+",
            re.IGNORECASE,
        ),
        r"\1[REDACTED:bearer]",
    ),
    (
        "bearer",
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]{8,}\b"),
        "[REDACTED:bearer]",
    ),
    (
        "private_key",
        re.compile(
            r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----"
            r"(?:.|\n)*?"
            r"-----END[ A-Z0-9]*PRIVATE KEY-----",
        ),
        "[REDACTED:private_key]",
    ),
    (
        "api_key",
        re.compile(
            r"(api[_\-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9._\-]{12,}['\"]?",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED:api_key]",
    ),
    (
        "db_url",
        re.compile(
            r"\b((?:postgres|postgresql|mysql|mongodb|mongodb\+srv|redis)://)"
            r"[^/\s:@]+:[^/\s:@]+@",
            re.IGNORECASE,
        ),
        r"\1[REDACTED:db_url]@",
    ),
)


def redact_secrets(value: str) -> str:
    """Apply the W8-6 redaction pass; idempotent."""
    if not value:
        return value
    redacted = value
    for _class, pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class ContentSample(StrictContractModel):
    """Snippet of extension-controlled content embedded in evidence."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    value: str = Field(default="", max_length=8 * 1024)
    source_location: str = Field(default="", max_length=512)
    sample_kind: str = Field(default="", max_length=64)

    @field_validator("value", mode="before")
    @classmethod
    def _redact_value(cls, value: object) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValueError(
                f"ContentSample.value must be str, got {type(value).__name__}"
            )
        return redact_secrets(value)


# W12-3: typed `EvidenceEvent.raw_context`. The producer
# (`executor/flows/playwright/attribution/links.py`) builds a fixed,
# known-key dict per `EvidenceEvent.kind`; W12-3 hoists those shapes into
# Pydantic variants and folds them into a discriminated union keyed by
# `event_class`. The literal §11.9 plan named only Network/File/Process —
# §11.9 was written before the W7+W11 `EvidenceEvent` consolidation, so the
# union covers all 7 producer kinds today (3 named + 4 extra).


class ScenarioRawContext(StrictContractModel):
    event_class: Literal["scenario"] = "scenario"
    status: str = ""
    started_at: float = 0.0
    ended_at: float = 0.0


class ActivationRawContext(StrictContractModel):
    event_class: Literal["activation"] = "activation"
    success: bool = True
    duration_ms: int | None = None
    source: str = ""


class UiBlockerRawContext(StrictContractModel):
    event_class: Literal["ui_blocker"] = "ui_blocker"
    status: str = ""
    stream: str = ""


class NetworkRawContext(StrictContractModel):
    event_class: Literal["network"] = "network"
    event_type: str = ""
    source_ip: str = ""
    path: str = ""
    http_method: str = ""
    http_status_code: int | None = None
    http_content_type: str = ""
    request_body_sha256: str = ""
    request_body_preview: str = ""
    request_body_truncated: bool = False
    response_body_sha256: str = ""
    response_body_preview: str = ""
    response_body_truncated: bool = False


class FileRawContext(StrictContractModel):
    event_class: Literal["file"] = "file"
    secondary_path: str = ""
    flags: str = ""
    observer: str = ""
    source: str = ""


class ProcessRawContext(StrictContractModel):
    event_class: Literal["process"] = "process"
    pid: int
    ppid: int | None = None
    command: str = ""
    arguments_preview: str = ""
    cwd: str = ""


class OutputChannelRawContext(StrictContractModel):
    event_class: Literal["output_channel_appendline"] = "output_channel_appendline"
    channel: str = ""
    text: str = ""


RawContext = Annotated[
    NetworkRawContext
    | FileRawContext
    | ProcessRawContext
    | ScenarioRawContext
    | ActivationRawContext
    | UiBlockerRawContext
    | OutputChannelRawContext,
    Field(discriminator="event_class"),
]


__all__ = [
    "SECRET_CLASSES",
    "ActivationRawContext",
    "ContentSample",
    "FileRawContext",
    "NetworkRawContext",
    "OutputChannelRawContext",
    "ProcessRawContext",
    "RawContext",
    "ScenarioRawContext",
    "UiBlockerRawContext",
    "redact_secrets",
]
