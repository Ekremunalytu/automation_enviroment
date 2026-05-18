"""W15-7 architecture gate: lifecycle marker id captures enforce ``<publisher>.<name>``.

This gate prevents the W15-5 I4 regression class: the two
``_LIFECYCLE_MARKER_PATTERNS`` entries that match the unanchored
``activate ... entered`` / ``activate ... returned|completed`` forms must
keep the strict ``[\\w-]+\\.[\\w.\\-]+`` id capture (the VS Code marketplace
``<publisher>.<name>`` shape). Loosening this back to ``[\\w.\\-]+`` lets
status codes (``200``), timestamps, or other peer tokens be captured as
the activation target — the false-positive class that motivated W15-5.

The W15-5 close-out evidence noted no existing extendable gate for the
regex shape; the new gate is deferred to W15-7 close-out hygiene. This
file lands that gate.

Two invariants, modeled on the behavioral parametrize approach used in
``tests/executor/test_playwright_extension_host.py`` (the W15-5 fix's
behavioral coverage) but lifted to the architecture lane as a *shape*
invariant rather than a behavior assertion:

1. **Strict id pattern present in unanchored W15-5 entries.** The two
   patterns that match ``activate ... entered`` and ``activate ...
   returned|completed`` without a parenthesis-wrapped id (``\\(...\\)``)
   or an explicit ``(?:for|by|from)\\s+`` keyword anchor must enforce the
   strict ``[\\w-]+\\.[\\w.\\-]+`` capture. The strict capture requires at
   least one dot inside the id, so a peer token without a publisher
   prefix cannot satisfy the pattern.
2. **No loose unanchored form regresses.** No ``_LIFECYCLE_MARKER_
   PATTERNS`` entry may use the unanchored loose form
   (``activate ... entered|returned|completed`` followed by
   ``[\\w.\\-]+`` without the ``\\.`` requirement). This is the W15-5
   pre-fix shape; reintroducing it brings the false-positive class back.

Architecture lane (not behavior): the test imports the patterns and
inspects their source strings via ``pattern.pattern``. Behavioral cases
already live in ``tests/executor/test_playwright_extension_host.py``.
"""

from __future__ import annotations

import re

from executor.flows.playwright.runtime_capture.extension_host_log_parse import (
    _LIFECYCLE_MARKER_PATTERNS,
)

STRICT_ID_CAPTURE = r"(?P<id>[\w-]+\.[\w.\-]+)"
LOOSE_ID_CAPTURE = r"(?P<id>[\w.\-]+)"

_PAREN_ANCHOR = re.compile(r"\\\(\s*\(\?P<id>")
_KEYWORD_ANCHOR = re.compile(r"\(\?:for\|by\|from\)\\s\+\(\?P<id>")
_UNANCHORED_ACTIVATE_ENTERED = re.compile(r"entered(?:\(\?:\\s\+for\)\?)?\\s\+\(\?P<id>")
_UNANCHORED_ACTIVATE_EXIT = re.compile(
    r"(?:returned\|completed)(?:\(\?:\\s\+for\)\?)?\\s\+\(\?P<id>"
)


def _classify(pattern_source: str) -> str:
    """Return ``"paren"``, ``"keyword"``, or ``"unanchored"`` for the id capture.

    The classification reflects how the surrounding regex bounds the id
    capture:
    - ``paren``: id is wrapped in an explicit ``\\(...\\)`` literal (e.g.,
      ``activate(<id>) entered``), so the closing paren bounds the
      capture.
    - ``keyword``: id is preceded by ``(?:for|by|from)\\s+`` (the register
      patterns), so the explicit keyword bounds the capture.
    - ``unanchored``: id appears after ``entered`` or
      ``returned|completed`` without either anchor. These are the W15-5
      I4 patterns that must use the strict id shape.
    """
    # Look for ``\(`` (escaped open-paren as a literal) followed by
    # ``(?P<id>`` within a short window — the ``activate(<id>)`` form.
    if (
        "\\(" in pattern_source
        and "\\(?P<id>" not in pattern_source
        and re.search(r"\\\(\s*\(\?P<id>", pattern_source)
    ):
        return "paren"
    if re.search(r"\(\?:for\|by\|from\)\\s\+\(\?P<id>", pattern_source):
        return "keyword"
    if _UNANCHORED_ACTIVATE_ENTERED.search(pattern_source) or _UNANCHORED_ACTIVATE_EXIT.search(
        pattern_source
    ):
        return "unanchored"
    # Fallback: if none of the anchors classify it, treat as unanchored so
    # the strict-id assertion fires defensively rather than silently
    # passing on a shape we don't recognise.
    return "unanchored"


def test_lifecycle_marker_patterns_unanchored_entries_use_strict_id_shape() -> None:
    """W15-5 I4 invariant: unanchored ``activate ... entered/returned/completed``
    patterns must enforce the strict ``<publisher>.<name>`` id shape.

    Drift class: a future maintainer loosens the id capture back to
    ``[\\w.\\-]+`` (the W15-5 pre-fix shape) to "match more cases", which
    reintroduces the false-positive class — status codes, timestamps,
    or peer tokens captured as the activation target.
    """
    assert _LIFECYCLE_MARKER_PATTERNS, (
        "_LIFECYCLE_MARKER_PATTERNS is empty; the lifecycle marker "
        "enrichment surface vanished. If the surface was removed "
        "deliberately, delete this gate too."
    )

    classifications: dict[str, list[str]] = {"paren": [], "keyword": [], "unanchored": []}
    for compiled, marker_type in _LIFECYCLE_MARKER_PATTERNS:
        source = compiled.pattern
        bucket = _classify(source)
        classifications[bucket].append(f"{marker_type!r}: {source!r}")

    unanchored = classifications["unanchored"]
    assert len(unanchored) >= 2, (
        "Expected at least two unanchored ``activate ... entered`` / "
        "``activate ... returned|completed`` patterns (W15-5 I4 tightened "
        "the surface to two such entries). Classifications:\n"
        + "\n".join(
            f"  {bucket}: {entries}" for bucket, entries in classifications.items()
        )
    )

    violations: list[str] = []
    for compiled, marker_type in _LIFECYCLE_MARKER_PATTERNS:
        source = compiled.pattern
        if _classify(source) != "unanchored":
            continue
        if STRICT_ID_CAPTURE not in source:
            violations.append(
                f"  marker_type={marker_type!r}, pattern={source!r} — "
                f"missing strict id capture {STRICT_ID_CAPTURE!r}"
            )

    assert not violations, (
        "Unanchored lifecycle marker patterns must enforce the strict "
        f"id shape {STRICT_ID_CAPTURE!r} (VS Code marketplace "
        "``<publisher>.<name>`` form). The W15-5 I4 fix tightened these "
        "from the loose ``[\\w.\\-]+`` form to prevent status codes and "
        "timestamps from being captured as the activation target. "
        "Reintroducing the loose form brings the false-positive class "
        "back.\n" + "\n".join(violations)
    )


def test_lifecycle_marker_patterns_reject_status_code_as_id() -> None:
    """Behavioral spot-check: no pattern should match ``activate entered 200``.

    The W15-5 pre-fix loose patterns matched ``activate entered 200`` and
    captured ``200`` as the extension id (a status code substituted for
    the activation target). The strict id shape requires at least one
    dot, so numeric tokens cannot satisfy it.

    Belt-and-suspenders alongside the shape invariant above: even if a
    future maintainer evades the source-string check (e.g., by building
    the regex via string concatenation that defeats the
    ``STRICT_ID_CAPTURE in source`` check), the behavioral assertion
    still fires.
    """
    false_positive_lines = (
        "activate entered 200",
        "activate returned 12:34:56.789",
        "activateFunction entered 9999",
        "activateFunction completed 5xx",
        # The activate-without-target false-positive shape (a verb
        # followed by a number sequence VS Code might emit for timing).
    )
    for line in false_positive_lines:
        for compiled, marker_type in _LIFECYCLE_MARKER_PATTERNS:
            match = compiled.search(line)
            if match is None:
                continue
            captured_id = match.groupdict().get("id")
            assert captured_id is None or (
                "." in captured_id and not captured_id.replace(".", "").isdigit()
            ), (
                f"Lifecycle pattern marker_type={marker_type!r} matched "
                f"false-positive line {line!r} and captured id="
                f"{captured_id!r}. The W15-5 I4 fix should have made this "
                f"unmatchable — a future loosening of the id shape would "
                f"reintroduce the false-positive class."
            )


def test_lifecycle_marker_patterns_accept_canonical_publisher_name_id() -> None:
    """Sanity: canonical ``<publisher>.<name>`` ids stay matchable.

    Negative-of-the-negative: the strict id capture must not be *so* strict
    that legitimate activation log lines stop matching. The W15-5 fix
    keeps these legitimate matches working.
    """
    canonical_lines = (
        "activate entered ms-python.python",
        "activate entered for ms-python.python",
        "activate returned ms-python.vscode-pylance in 42 ms",
        "activate completed for esbenp.prettier-vscode",
        "activateFunction entered extrace.extrace-harness",
    )
    matched_any = []
    for line in canonical_lines:
        line_matched = False
        for compiled, marker_type in _LIFECYCLE_MARKER_PATTERNS:
            match = compiled.search(line)
            if match is None:
                continue
            captured_id = match.groupdict().get("id")
            if captured_id and "." in captured_id:
                line_matched = True
                matched_any.append((line, marker_type, captured_id))
                break
        assert line_matched, (
            f"Canonical lifecycle log line {line!r} did not match any "
            f"_LIFECYCLE_MARKER_PATTERNS entry. The W15-5 I4 tightening "
            f"may have over-narrowed — verify legitimate publisher.name "
            f"ids still satisfy the id capture."
        )
    assert matched_any, "No canonical lifecycle line matched any pattern."
