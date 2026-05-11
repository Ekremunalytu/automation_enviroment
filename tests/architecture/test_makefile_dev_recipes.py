"""W13-5 architecture regression: Makefile dev-server recipes pin
loopback default and LAN opt-in semantics per ADR 0007.

Three surfaces are pinned here:

1. `make dev` — uvicorn invocation must carry `--host 127.0.0.1`
   literal. ADR 0007 requires the loopback default to be set at the
   recipe level so a casual `make dev` cannot be silently widened by
   an env var.
2. `make run` — same loopback discipline as `dev`; production-style
   local launch stays loopback-bound.
3. `make dev-lan` — recipe must set `EXTRACE_ALLOW_LAN=1`, must honor
   `API_HOST` env override via `$${API_HOST:-0.0.0.0}` shell parameter
   expansion (Make `$$` escape + POSIX `${VAR:-default}`) so
   `API_HOST=… make dev-lan` narrows the bind socket alongside the
   settings layer, must default to wildcard `0.0.0.0` when the
   override is absent (LAN intent stays the default for this recipe),
   and must keep the ADR 0007 stdout banner as the operator's
   in-process signal.

Codex Cloud audit `2026-05-10` H3 flagged the `dev-lan` recipe's
hard-coded `--host 0.0.0.0` literal: APISettings.HOST (Pydantic
post-init) honours an explicit `API_HOST` env override, but uvicorn
binds whatever string the recipe passes via `--host`. The drift
means `API_HOST=192.168.1.10 make dev-lan` yields uvicorn bound to
`0.0.0.0` while settings think they bind `192.168.1.10`. W13-5
closes this by replacing the literal with `$${API_HOST:-0.0.0.0}`.

The existing settings gate `tests/architecture/test_default_bindings.py`
already pins the post-init semantics (HOST default 127.0.0.1,
EXTRACE_ALLOW_LAN truthy/falsy, explicit override wins). This file
extends the discipline to the Makefile recipe layer so future drift
between the two layers is caught structurally.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
MAKEFILE_PATH = REPO_ROOT / "Makefile"

_RECIPE_HEADER_RE = re.compile(r"^([a-zA-Z_][\w-]*):(?:\s+[\w./-]+)*\s*(?:##.*)?$")


def _recipe_bodies() -> dict[str, list[str]]:
    """Parse Makefile recipe headers and their TAB-indented bodies.

    Returns `{recipe_name: [body_line, ...]}`. Body lines preserve the
    original TAB indentation; callers join them with newlines and
    substring-match against the result. Recipe headers with
    prerequisites (`name: dep1 dep2`) are accepted; variable
    assignments (`NAME := value` / `NAME = value`) are not — the
    regex anchors the colon directly after the name with no
    intervening whitespace.
    """
    bodies: dict[str, list[str]] = {}
    current: str | None = None
    text = MAKEFILE_PATH.read_text()
    for line in text.splitlines():
        match = _RECIPE_HEADER_RE.match(line)
        if match:
            current = match.group(1)
            bodies[current] = []
            continue
        if current is None:
            continue
        if line.startswith("\t"):
            bodies[current].append(line)
        elif not line.strip():
            continue
        else:
            current = None
    return bodies


def _body_text(recipe: str) -> str:
    bodies = _recipe_bodies()
    assert recipe in bodies, (
        f"recipe `{recipe}:` not found in Makefile — parser drift or "
        f"recipe renamed; update tests/architecture/test_makefile_dev_recipes.py"
    )
    return "\n".join(bodies[recipe])


def test_dev_recipe_binds_loopback_literal() -> None:
    body = _body_text("dev")
    assert "--host 127.0.0.1" in body, (
        "make dev recipe must carry `--host 127.0.0.1` literal "
        "(ADR 0007 loopback default at recipe level):\n" + body
    )


def test_run_recipe_binds_loopback_literal() -> None:
    body = _body_text("run")
    assert "--host 127.0.0.1" in body, (
        "make run recipe must carry `--host 127.0.0.1` literal "
        "(ADR 0007 loopback default at recipe level):\n" + body
    )


def test_dev_lan_recipe_sets_extrace_allow_lan() -> None:
    """`make dev-lan` is the host-mode opt-in surface. The recipe
    must flip `EXTRACE_ALLOW_LAN=1` so APISettings.model_post_init
    substitutes wildcard CORS (and wildcard HOST when no explicit
    override). This is the only Makefile surface that turns the
    opt-in on; the architecture test pins it so a future refactor
    cannot silently drop it."""
    body = _body_text("dev-lan")
    assert "EXTRACE_ALLOW_LAN=1" in body, (
        "make dev-lan recipe must set `EXTRACE_ALLOW_LAN=1`:\n" + body
    )


def test_dev_lan_recipe_honors_api_host_override() -> None:
    """W13-5 closes the H3 drift by replacing `--host 0.0.0.0`
    literal with `--host $${API_HOST:-0.0.0.0}` (Make `$$` escape
    + POSIX `${VAR:-default}` shell parameter expansion). This
    test pins the new form and forbids the pre-W13-5 literal so
    the drift cannot regress."""
    body = _body_text("dev-lan")
    assert "$${API_HOST:-0.0.0.0}" in body, (
        "make dev-lan recipe must honor API_HOST override via "
        "`$${API_HOST:-0.0.0.0}` shell parameter expansion "
        "(Make $$ escape):\n" + body
    )
    assert "--host 0.0.0.0" not in body, (
        "make dev-lan recipe must not hard-code `--host 0.0.0.0` — "
        "use `--host $${API_HOST:-0.0.0.0}` so API_HOST env override "
        "reaches uvicorn:\n" + body
    )


def test_dev_lan_recipe_defaults_to_wildcard_host() -> None:
    """When `API_HOST` is unset the shell expansion must fall back
    to `0.0.0.0`. This pins LAN intent at the recipe level: an
    operator who types `make dev-lan` without further env is still
    widening the bind (the entire point of the `dev-lan` target).
    Without this pin a future refactor could swap the default to
    `127.0.0.1` and silently make `dev-lan` equivalent to `dev`."""
    body = _body_text("dev-lan")
    assert ":-0.0.0.0}" in body, (
        "make dev-lan recipe `${VAR:-default}` fallback must keep "
        "`0.0.0.0` so LAN intent stays the default:\n" + body
    )


def test_dev_lan_recipe_emits_adr_0007_warning() -> None:
    """The recipe's stdout banner is the only in-process signal that
    the loopback default has been bypassed (runbook §Configure
    §Host-mode documents this as the operator's confirmation).
    The banner must remain structurally present even as the recipe
    body is refactored."""
    body = _body_text("dev-lan")
    assert "ADR 0007" in body, (
        "make dev-lan recipe must keep the `ADR 0007` stdout banner "
        "(operator signal that loopback default has been bypassed):\n" + body
    )
    assert "LAN binding requested" in body, (
        "make dev-lan recipe must keep the `LAN binding requested` "
        "banner phrasing:\n" + body
    )
