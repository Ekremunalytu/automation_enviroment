"""W14-4 architecture gate: producer-side conformance for the
``EvidenceEvent`` kind allowlist.

Closes the producer half of `[FOLLOWUP
evidence-event-kind-raw-context-invariant]`. The Pydantic
``@model_validator`` at ingest catches mismatched / unknown kinds, but
the canonical executor producer
(`executor/flows/playwright/attribution/links.py`) is where every
``EvidenceEvent`` is constructed in production. This gate pins the
producer to the closed allowlist so a future drift (e.g. a new
``EvidenceEvent(kind="agent")`` site) fails at AST review instead of
at the next live scan.

Two invariants are pinned here:

1. ``test_attribution_producer_kinds_subset_of_allowlist`` — every
   string literal passed as ``kind=`` to an ``EvidenceEvent(...)``
   constructor inside the attribution module is a key in
   ``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS``.
2. ``test_attribution_producer_emits_at_least_one_kind`` — the
   attribution producer emits at least one kind. A regression that
   silently empties out the producer (zero ``EvidenceEvent(...)``
   constructors) would otherwise pass case 1 vacuously.

Pattern modeled on the W14-2 ``test_output_signal_ts_guard.py``
body-invariant gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

from packages.analysis_contracts.contracts import (
    _EVIDENCE_EVENT_KIND_TO_EVENT_CLASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTION_MODULE = (
    REPO_ROOT
    / "executor"
    / "flows"
    / "playwright"
    / "attribution"
    / "links.py"
)
CONSTRUCTOR_NAME = "EvidenceEvent"
KIND_KEYWORD = "kind"


def _kind_literal_from_call(node: ast.Call) -> str | None:
    """Return the string-literal value passed as ``kind=...`` to the call,
    or ``None`` if the kind is not a static constant.
    """
    for keyword in node.keywords:
        if keyword.arg != KIND_KEYWORD:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(
            keyword.value.value, str
        ):
            return keyword.value.value
    return None


def _collect_evidence_event_kind_literals() -> list[tuple[int, str | None]]:
    """Walk the attribution module and return ``(lineno, kind_literal)``
    pairs for every ``EvidenceEvent(...)`` constructor call. ``kind_literal``
    is ``None`` when the call passes a non-constant expression for kind.
    """
    tree = ast.parse(ATTRIBUTION_MODULE.read_text(encoding="utf-8"))
    sites: list[tuple[int, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        if isinstance(callee, ast.Name) and callee.id == CONSTRUCTOR_NAME:
            sites.append((node.lineno, _kind_literal_from_call(node)))
        elif (
            isinstance(callee, ast.Attribute)
            and callee.attr == CONSTRUCTOR_NAME
        ):
            sites.append((node.lineno, _kind_literal_from_call(node)))
    return sites


def test_attribution_producer_kinds_subset_of_allowlist() -> None:
    """Every kind literal emitted by the attribution producer must live in
    ``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS``. A regression that adds a new
    kind without registering it in the allowlist would otherwise fail
    only at ingest (the Pydantic validator); this gate catches it at
    AST review.
    """
    sites = _collect_evidence_event_kind_literals()
    violations: list[str] = []
    for lineno, kind in sites:
        if kind is None:
            violations.append(
                f"{ATTRIBUTION_MODULE.relative_to(REPO_ROOT)}:{lineno}: "
                f"EvidenceEvent(...) passes a non-constant kind expression; "
                "every producer site must emit a string literal so the "
                "allowlist gate can pin it statically."
            )
            continue
        if kind not in _EVIDENCE_EVENT_KIND_TO_EVENT_CLASS:
            violations.append(
                f"{ATTRIBUTION_MODULE.relative_to(REPO_ROOT)}:{lineno}: "
                f"kind={kind!r} is not in the W14-4 allowlist; either add "
                "it to `_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` (and the test "
                "fixtures) or correct the producer."
            )
    assert not violations, (
        "Producer kind literals must match the W14-4 allowlist:\n"
        + "\n".join(violations)
    )


def test_attribution_producer_emits_at_least_one_kind() -> None:
    """Pin that the attribution producer is actually emitting events.

    Without this, a refactor that silently removes every
    ``EvidenceEvent(...)`` constructor (e.g. by relocating them under
    an unreachable branch) would pass the allowlist gate above
    vacuously.
    """
    sites = _collect_evidence_event_kind_literals()
    assert sites, (
        f"{ATTRIBUTION_MODULE.relative_to(REPO_ROOT)} must construct at "
        "least one EvidenceEvent (W14-4 producer surface invariant). The "
        "allowlist gate would otherwise be vacuously true."
    )
