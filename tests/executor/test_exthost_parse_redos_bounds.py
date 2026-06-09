"""S5 (W23) — ReDoS-linearity backstop for the ext-host parse/marker regexes.

The S5 sweep audited the four regex-bearing ext-host files and concluded the
family is line-anchored / linear. ``extension_host_log_parse`` got a code fix
(bounded prefix + per-line cap) with timing regressions in
``test_playwright_extension_host.py``. The other three regexes were declared
linear in the tracker but were only *functionally* covered — these tests make
the linearity claim executable so a future edit that reintroduces an unanchored
greedy prefix / nested quantifier is caught.

Each test feeds a ~1M-char adversarial *near-miss* line (the worst case for
greedy backtracking) and asserts the match returns in well under a ceiling that
a quadratic regression (minutes on this input) could never meet, plus a
correctness assertion so the test is not purely a timer.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

from executor.flows.playwright.health.handshake import (
    _harness_trace_records_by_attempt,
)
from executor.flows.playwright.runtime_capture.extension_host_strace_parse import (
    parse_strace_process_event_line,
)
from executor.host import _HARNESS_SECRET_ENV_NAME, _mask_harness_secret_in_message

# Linear on a 1M-char line is ~ms; a quadratic regression is minutes. 0.5 s
# fails the quadratic path with comfortable CI margin.
_CEILING_S = 0.5
_BIG = 1_000_000


def test_harness_secret_mask_is_linear_and_masks_value() -> None:
    """``_HARNESS_SECRET_MASK_RE`` = ``NAME=\\S+`` over a bounded error string.
    A mega ``\\S+`` run stays linear, and the secret value is still masked."""
    message = f"{_HARNESS_SECRET_ENV_NAME}=" + ("a" * _BIG)

    start = time.perf_counter()
    masked = _mask_harness_secret_in_message(message)
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_S, f"mask took {elapsed * 1000:.1f} ms"
    assert masked == f"{_HARNESS_SECRET_ENV_NAME}=***"
    assert "aaaa" not in masked


def test_harness_marker_search_is_linear_on_unterminated_payload() -> None:
    """``_HARNESS_MARKER_RE`` = ``[extrace-harness]\\s+{.*}`` applied per-line.
    An open ``{`` with no closing ``}`` forces the greedy ``.*`` to scan to EOL
    and backtrack — single quantifier, so O(n). A well-formed marker on a normal
    line still parses, proving the search path itself works."""
    # Adversarial: marker prefix, open brace, then a huge brace-less run.
    unterminated = "[extrace-harness] {" + ("a" * _BIG)
    report = SimpleNamespace(extension_host_output=unterminated)

    start = time.perf_counter()
    traces = _harness_trace_records_by_attempt(report)
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_S, f"marker scan took {elapsed * 1000:.1f} ms"
    assert traces == {}  # no closing brace -> no JSON payload -> no records

    # Correctness: a well-formed marker line is parsed into its attempt bucket.
    good = SimpleNamespace(
        extension_host_output='[extrace-harness] {"attempt_id": "a1", "phase": "complete"}'
    )
    assert _harness_trace_records_by_attempt(good)["a1"][0]["phase"] == "complete"


def test_strace_process_event_parse_is_linear_on_unterminated_args() -> None:
    """``_PROCESS_EVENT_RE`` is ``^...$``-anchored with a single greedy
    ``(?P<args>.*)``. A line that matches the prefix then never closes ``)`` /
    `` = result`` forces the ``.*`` to backtrack to the anchor — still O(n). A
    well-formed execve line still parses into a ProcessEvent."""
    unterminated = "1234.5 execve(" + ("a" * _BIG)

    start = time.perf_counter()
    result = parse_strace_process_event_line(
        unterminated, root_pid=1, ppid_by_pid={}, cwd_by_pid={}
    )
    elapsed = time.perf_counter() - start

    assert elapsed < _CEILING_S, f"strace parse took {elapsed * 1000:.1f} ms"
    assert result is None  # no closing ")  = <result>" -> no match

    # Correctness: a real execve line parses into an exec ProcessEvent.
    good = parse_strace_process_event_line(
        '1234.5 execve("/usr/bin/node", ["node", "x.js"], 0x7ff) = 0',
        root_pid=1,
        ppid_by_pid={},
        cwd_by_pid={},
    )
    assert good is not None
    assert good.operation == "exec"
    assert good.command == "/usr/bin/node"
