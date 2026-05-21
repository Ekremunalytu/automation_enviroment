"""W14-3 architecture gate: Makefile `sim-target` and `sim-run` recipes
must validate and quote operator-supplied variables.

Closes the U4-U12 audit (`[FOLLOWUP
codex-2026-05-10-U4-U12-makefile-shell-quoting]`).

Pre-W14-3, both recipes passed ``$(TARGET)`` / ``$(SCENARIO)`` /
``$(TRIGGERS)`` to ``docker exec`` unquoted, so an operator who typed
``make sim-target TARGET='foo;rm -rf /'`` would have the shell split the
value on spaces and interpret the semicolon as a command terminator.
W14-3 adds two complementary defenses:

1. **Validation:** each variable is required to match a strict character
   class (``[A-Za-z0-9._-]+`` for TARGET, ``[A-Za-z0-9_]+`` for
   SCENARIO, ``[A-Za-z0-9./_-]+`` for TRIGGERS); a mismatch fails the
   recipe before any unquoted expansion reaches the shell.
2. **Quoting:** every operator-controlled positional argument inside the
   ``docker exec`` invocation is double-quoted, so even if a future
   regex tweak loosens validation, word-splitting cannot inject side
   commands.

Pattern modeled on the W13-5
``tests/architecture/test_makefile_dev_recipes.py`` content-scan style.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE_PATH = REPO_ROOT / "Makefile"

_RECIPE_HEADER_RE = re.compile(r"^([a-zA-Z_][\w-]*):")


def _recipe_bodies(text: str) -> dict[str, list[str]]:
    """Return {target_name: [body_lines]} for every recipe in the Makefile.

    Mirrors the helper used by `test_makefile_dev_recipes.py` (W13-5): a
    Make recipe body is the TAB-indented region following a `target:`
    line, terminated by the first non-TAB / non-comment / non-empty
    line.
    """
    bodies: dict[str, list[str]] = {}
    current_target: str | None = None
    for line in text.splitlines():
        if line.startswith("\t"):
            if current_target is not None:
                bodies.setdefault(current_target, []).append(line)
            continue
        header_match = _RECIPE_HEADER_RE.match(line)
        if header_match is not None:
            current_target = header_match.group(1)
            bodies.setdefault(current_target, [])
        else:
            current_target = None
    return bodies


def _body_text(recipe_name: str) -> str:
    bodies = _recipe_bodies(MAKEFILE_PATH.read_text(encoding="utf-8"))
    assert recipe_name in bodies, (
        f"{MAKEFILE_PATH.relative_to(REPO_ROOT)} must define a `{recipe_name}` "
        "recipe — W14-3 U4-U12 anchors its quoting/validation gate to it."
    )
    return "\n".join(bodies[recipe_name])


def test_sim_target_validates_operator_variables() -> None:
    """`sim-target` must reject TARGET / SCENARIO / TRIGGERS values that
    fall outside their expected character classes before they reach
    `docker exec`.
    """
    body = _body_text("sim-target")
    assert "grep -qE '^[A-Za-z0-9._-]+$$'" in body, (
        "`sim-target` must validate TARGET with the [A-Za-z0-9._-]+ "
        "character class (W14-3 U4)."
    )
    assert "grep -qE '^[A-Za-z0-9_]+$$'" in body, (
        "`sim-target` must validate SCENARIO with [A-Za-z0-9_]+ when set (W14-3 U6)."
    )
    assert "grep -qE '^[A-Za-z0-9./_-]+$$'" in body, (
        "`sim-target` must validate TRIGGERS with [A-Za-z0-9./_-]+ when set (W14-3 U5)."
    )


def test_sim_target_quotes_operator_variables() -> None:
    """The `docker exec` command line inside `sim-target` must
    double-quote every Make-variable interpolation.
    """
    body = _body_text("sim-target")
    assert '--target-extension-id "$(TARGET)"' in body, (
        "`sim-target` must double-quote $(TARGET) inside the docker exec "
        "command line (W14-3 U4)."
    )
    assert '--triggers "$(TRIGGERS)"' in body, (
        "`sim-target` must double-quote $(TRIGGERS) inside the conditional "
        "expansion (W14-3 U5)."
    )
    assert '--scenario "$(SCENARIO)"' in body, (
        "`sim-target` must double-quote $(SCENARIO) inside the conditional "
        "expansion (W14-3 U6)."
    )
    # Explicit negative: the pre-W14-3 unquoted shape must NOT survive.
    assert "--target-extension-id $(TARGET)" not in body.replace(
        '--target-extension-id "$(TARGET)"', ""
    ), (
        "`sim-target` re-introduced the unquoted $(TARGET) interpolation; "
        "every Make variable on the docker exec line must stay quoted."
    )


def test_sim_run_validates_scenario_variable() -> None:
    """`sim-run` must reject SCENARIO values outside [A-Za-z0-9_]+."""
    body = _body_text("sim-run")
    assert "grep -qE '^[A-Za-z0-9_]+$$'" in body, (
        "`sim-run` must validate SCENARIO with [A-Za-z0-9_]+ before "
        "passing it to docker exec (W14-3 U6)."
    )


def test_sim_run_quotes_scenario_variable() -> None:
    """The `docker exec` line inside `sim-run` must double-quote $(SCENARIO)."""
    body = _body_text("sim-run")
    assert '--scenario "$(SCENARIO)"' in body, (
        "`sim-run` must double-quote $(SCENARIO) inside the docker exec "
        "command line (W14-3 U6)."
    )
