"""W15-6 architecture gate: enforce ADR 0011 posture on the catalog router.

Three AST-level invariants pin the unauthenticated-by-design posture
of ``workflows/extension_catalog/router.py`` so that a future refactor
cannot silently flip it without an ADR 0011 amendment:

1. **Module docstring cites ADR 0011** — doc decay over time cannot
   silently strand the posture rationale. The substring ``ADR 0011``
   must appear in the parsed module docstring.
2. **``APIRouter(...)`` construction has no auth dependency** — if a
   future PR adds ``dependencies=[Depends(auth_…)]`` or any keyword
   value whose callable name matches the auth-like regex (``auth``,
   ``require_*``, ``verify_*``, ``hmac_*``, ``marker_*``), the gate
   fails. Silent drift to Option B via a one-liner is prevented.
3. **Endpoint count is locked at twelve** — eleven catalog endpoints
   plus the ``/`` API root. Adding a new endpoint fails the gate,
   forcing an ADR 0011 amendment review at the same time. This is
   the "no silent surface expansion" invariant.

Modeled on the W14-5 / W14-2 AST gate pattern: parse → walk → collect
violations → assert with a formatted report.

ADR 0011 is the load-bearing reference; amending the gate without
amending the ADR or vice versa is the failure mode this gate exists
to prevent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "workflows" / "extension_catalog" / "router.py"

ADR_REFERENCE = "ADR 0011"

_AUTH_LIKE_NAME = re.compile(r"^(auth|require_|verify_|hmac_|marker_)")

_HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "post", "put", "delete", "patch", "head", "options"}
)

EXPECTED_ENDPOINT_COUNT = 12


def _parse_router_module() -> ast.Module:
    """Parse ``workflows/extension_catalog/router.py`` into an AST."""
    source = ROUTER_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(ROUTER_PATH))


def _find_apirouter_construction(module: ast.Module) -> ast.Call | None:
    """Locate the single ``router = APIRouter(...)`` assignment call."""
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if isinstance(func, ast.Name) and func.id == "APIRouter":
            return node.value
        if isinstance(func, ast.Attribute) and func.attr == "APIRouter":
            return node.value
    return None


def _is_router_decorator(decorator: ast.expr) -> bool:
    """Match ``@router.<verb>(...)`` decorators."""
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return False
    if not isinstance(func.value, ast.Name) or func.value.id != "router":
        return False
    return func.attr.lower() in _HTTP_METHODS


def test_catalog_router_module_cites_adr_0011() -> None:
    """Module docstring must reference ADR 0011 verbatim.

    Drift class: an unrelated refactor edits the module docstring and
    drops the posture rationale. Without this gate, the next reader
    has no in-code pointer to the ADR that justifies the absence of
    auth on the router.
    """
    module = _parse_router_module()
    docstring = ast.get_docstring(module)
    assert docstring is not None, (
        f"{ROUTER_PATH.relative_to(REPO_ROOT)} has no module docstring; "
        f"ADR 0011 posture documentation must live in the module "
        f"docstring so a future reader sees it at the top of the file."
    )
    assert ADR_REFERENCE in docstring, (
        f"{ROUTER_PATH.relative_to(REPO_ROOT)} module docstring does "
        f"not contain {ADR_REFERENCE!r}. The posture rationale must "
        f"cite the ADR explicitly so doc decay cannot silently strand "
        f"the decision."
    )


def test_catalog_router_has_no_auth_dependency() -> None:
    """``APIRouter(...)`` must not attach an auth-like dependency.

    Drift class: a future PR adds ``dependencies=[Depends(auth_xyz)]``
    to the router construction site as a one-liner, silently flipping
    the posture to Option B without an ADR 0011 amendment. The gate
    walks the keyword arguments of the ``APIRouter(...)`` call and
    rejects any callable name matching the auth-like regex.
    """
    module = _parse_router_module()
    call = _find_apirouter_construction(module)
    assert call is not None, (
        f"{ROUTER_PATH.relative_to(REPO_ROOT)} does not contain a "
        f"``router = APIRouter(...)`` assignment; this gate cannot "
        f"validate posture invariants. If the construction has moved, "
        f"update ``_find_apirouter_construction`` to match the new shape."
    )

    violations: list[str] = []
    for keyword in call.keywords:
        if keyword.arg != "dependencies":
            continue
        if not isinstance(keyword.value, (ast.List, ast.Tuple)):
            violations.append(
                "``dependencies`` kwarg present but value is not a list/tuple "
                "literal; manual review required."
            )
            continue
        for elt in keyword.value.elts:
            name = _extract_callable_name(elt)
            if name is None:
                continue
            if _AUTH_LIKE_NAME.match(name):
                violations.append(
                    f"``dependencies=[..., {name}(...), ...]`` attached to "
                    f"``APIRouter(...)`` — silent drift to Option B. "
                    f"Amend ADR 0011 first."
                )

    assert not violations, (
        "Catalog router has an auth-like dependency attached. "
        "Posture is locked unauthenticated by ADR 0011; flipping to "
        "per-request auth requires an ADR amendment.\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_catalog_router_endpoint_count_locked() -> None:
    """Endpoint count is locked at twelve.

    Drift class: a new ``@router.<verb>`` endpoint is added without an
    ADR 0011 amendment review. The current surface is eleven catalog
    endpoints plus the ``/`` API root (twelve total). Adding a new
    one fails the gate so the posture decision is re-examined at the
    same time.
    """
    module = _parse_router_module()
    count = 0
    for node in ast.walk(module):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if _is_router_decorator(decorator):
                count += 1
                break

    assert count == EXPECTED_ENDPOINT_COUNT, (
        f"Catalog router has {count} ``@router.<verb>`` endpoints; "
        f"expected {EXPECTED_ENDPOINT_COUNT} (11 catalog endpoints + "
        f"``/`` root). Adding or removing an endpoint requires an "
        f"ADR 0011 amendment review — update the expected count here "
        f"and the ADR's endpoint inventory table together."
    )


def _extract_callable_name(node: ast.expr) -> str | None:
    """Extract the callable name from ``func(...)`` or ``mod.func(...)``."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
