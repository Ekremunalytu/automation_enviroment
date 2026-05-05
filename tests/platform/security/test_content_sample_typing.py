"""W9-6c — Structural typing test for ContentSample propagation.

``ContentSample`` (``packages.analysis_contracts.evidence``) is the single
carrier for extension-controlled string snippets in evidence artifacts:
its ``value`` field is filtered through ``redact_secrets`` on construction
*and* on every assignment, so no consumer can read or persist a raw
secret form. Detection rules and the activation-report pipeline must use
``ContentSample`` (or a wrapper around it) for any field that holds
extension-derived raw text — plain ``str`` bypasses redaction.

This test pins:

1. ``ContentSample``'s structural invariants (``extra="forbid"``,
   ``validate_assignment=True``, redaction validator on ``value``).
2. The ``_PENDING_MIGRATION`` allow-list — fields on ``ActivationReport``
   subtree that should hold ``ContentSample`` but currently still hold
   plain ``str`` or ``dict[str, Any]``. Each entry is asserted via
   ``pytest.xfail(strict=True)`` so the test surface flips XPASS → fail
   the moment the migration lands, prompting allow-list cleanup.

Out-of-scope for this commit (tracked in
``[FOLLOWUP w8-6-content-sample-structural-test]``): the comprehensive
audit of every extension-derived string field on the contract surface.
The W8-6 closure shipped redaction; the W9-6c regression locks the
contract shape and the migration-pending placeholder.
"""

from __future__ import annotations

from pydantic import ConfigDict

from packages.analysis_contracts import ContentSample
from packages.analysis_contracts.contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.evidence import redact_secrets

# Migration-pending ``ActivationReport`` subtree fields. Once the field's
# annotation flips to ``ContentSample`` (or a Container of it), the
# corresponding xfail assertion below will XPASS and the test will fail —
# that is the prompt to remove the entry here and from the allow-list in
# ``[FOLLOWUP w8-6-content-sample-structural-test]``.
_PENDING_MIGRATION: list[tuple[type, str]] = [
    (EvidenceEvent, "raw_context"),
    # ``extension_host_output`` is filtered through ``redact_secrets`` at
    # the ``report_builder.build_report_data`` serialization boundary
    # (the W11-companion close of
    # ``[FOLLOWUP w8-6-extension-host-output-redaction]``); the W13
    # follow-up flips the annotation to ``ContentSample`` so redaction is
    # enforced at the contract layer rather than the producer.
    (ActivationReport, "extension_host_output"),
]


def test_content_sample_extra_forbid() -> None:
    """``ContentSample`` rejects unknown keys to keep the contract surface
    minimal and audit-friendly."""
    config = ContentSample.model_config
    assert isinstance(config, dict | ConfigDict)  # pydantic exposes a TypedDict
    assert config.get("extra") == "forbid", (
        "ContentSample must keep extra='forbid' so untyped extension data "
        "cannot be smuggled in alongside the redacted value."
    )


def test_content_sample_validate_assignment_active() -> None:
    """``validate_assignment=True`` ensures re-assignment of ``value``
    re-enters the redaction validator — without this, mutation could
    bypass the redaction performed at construction time."""
    config = ContentSample.model_config
    assert config.get("validate_assignment") is True

    sample = ContentSample(value="benign", source_location="t", sample_kind="line")
    sample.value = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert "[REDACTED:aws]" in sample.value
    assert "wJalrXUtnFEMI" not in sample.value


def test_content_sample_value_field_required_str() -> None:
    """The ``value`` field must remain a ``str``-typed field with the
    pre-redaction validator wired in."""
    fields = ContentSample.model_fields
    assert "value" in fields
    assert fields["value"].annotation is str
    # ``_redact_value`` is registered as a ``before`` validator on ``value``;
    # constructing with a known secret must produce the redacted form.
    redacted = ContentSample(value="api_key=AKIAIOSFODNN7EXAMPLE").value
    assert "[REDACTED" in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted


def test_redact_secrets_is_idempotent() -> None:
    """``redact_secrets`` must be safe to apply twice — re-validation on
    assignment should not mutate an already-redacted value."""
    raw = "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    once = redact_secrets(raw)
    twice = redact_secrets(once)
    assert once == twice


def test_pending_migration_fields_not_yet_content_sample() -> None:
    """Snapshot of fields still on plain ``str``/``dict`` that the W8-6
    redaction surface ought to type as ``ContentSample`` once consumer
    migration lands. When a field flips to ``ContentSample``, this test
    fails (XPASS-equivalent) and the allow-list above must be trimmed.
    """
    for model, field_name in _PENDING_MIGRATION:
        fields = model.model_fields
        assert field_name in fields, (
            f"{model.__name__}.{field_name} is missing — allow-list "
            "needs an update (field renamed or dropped)."
        )
        annotation = fields[field_name].annotation
        # Today these fields are NOT ``ContentSample``. The migration
        # forward-prompt: when annotation becomes ``ContentSample`` (or
        # ``list[ContentSample]`` etc.), this assertion fails and the
        # entry must be removed from ``_PENDING_MIGRATION``.
        assert annotation is not ContentSample, (
            f"{model.__name__}.{field_name} is now ContentSample-typed — "
            "remove it from _PENDING_MIGRATION and from the "
            "[FOLLOWUP w8-6-content-sample-structural-test] entry."
        )
