"""Bounded, deterministic SAP-5 import and loader reachability graph."""

from __future__ import annotations

import ast
import json
import posixpath
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from packages.analysis_contracts.static_detection import (
    StaticArtifactReachabilityConfidence,
    StaticArtifactReachabilityEdgeKind,
    StaticCoverageReason,
    StaticReachabilityLimitReason,
    StaticReachabilitySummary,
    StaticReachabilityUnresolvedReference,
)
from static_runtime.context import StaticAnalysisContext

MAX_REACHABILITY_NODES = 4_096
MAX_REACHABILITY_EDGES = 16_384
MAX_REACHABILITY_BYTES = 128 * 1024 * 1024
MAX_REACHABILITY_DEPTH = 64
MAX_UNRESOLVED_DETAILS = 20
_MAX_EXPRESSION_CHARS = 512
_MAX_PACKAGE_MANIFEST_BYTES = 1024 * 1024

_MODULE_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs", ".json")
_LOADER_SUFFIXES = (*_MODULE_SUFFIXES, ".node", ".wasm")
_TRAVERSABLE_SUFFIXES = frozenset(_MODULE_SUFFIXES[:-1])
_BUILTIN_MODULES = frozenset(
    {
        "assert",
        "buffer",
        "child_process",
        "cluster",
        "crypto",
        "dgram",
        "dns",
        "events",
        "fs",
        "http",
        "https",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "querystring",
        "readline",
        "stream",
        "string_decoder",
        "timers",
        "tls",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "worker_threads",
        "zlib",
        "vscode",
    }
)

_CONST_RE = re.compile(
    r"\bconst\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?P<expr>[^;\n]{1,512})"
)
_FROM_RE = re.compile(
    r"\b(?P<kind>import|export)\b[^;\n]{0,400}?\bfrom\s*"
    r"(?P<quote>['\"])(?P<spec>[^'\"\n]{1,400})(?P=quote)"
)
_SIDE_EFFECT_IMPORT_RE = re.compile(
    r"\bimport\s*(?P<quote>['\"])(?P<spec>[^'\"\n]{1,400})(?P=quote)"
)
_CALL_RE = re.compile(
    r"(?P<call>require\.resolve|require|import)\s*\("
    r"(?P<expr>[^;\n]{1,512})\)"
)
_SOURCE_MAP_RE = re.compile(r"[#@]\s*sourceMappingURL\s*=\s*(?P<spec>[^\s*]{1,400})")
_TEMPLATE_SLOT_RE = re.compile(r"\$\{(?P<name>[A-Za-z_$][\w$]*)\}")


@dataclass(frozen=True, slots=True)
class ReachabilityProvenance:
    depth: int
    parent: str
    edge_kind: StaticArtifactReachabilityEdgeKind
    confidence: StaticArtifactReachabilityConfidence


@dataclass(frozen=True, slots=True)
class ReachabilityGraphResult:
    provenance: dict[str, ReachabilityProvenance]
    summary: StaticReachabilitySummary
    coverage_reasons: tuple[StaticCoverageReason, ...]


@dataclass(frozen=True, slots=True)
class _Reference:
    line_number: int
    kind: StaticArtifactReachabilityEdgeKind
    expression: str
    specifier: str | None
    confidence: StaticArtifactReachabilityConfidence
    rooted: bool = False


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _literal(value: str) -> str | None:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return None
    return parsed if isinstance(parsed, str) else None


def _split_top_level(value: str, separator: str) -> list[str] | None:
    parts: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote is not None:
            if char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    if quote is not None or depth != 0:
        return None
    parts.append(value[start:].strip())
    return parts


def _template_value(value: str, constants: dict[str, str]) -> str | None:
    if not (value.startswith("`") and value.endswith("`")):
        return None
    body = value[1:-1]
    unresolved = False

    def replace(match: re.Match[str]) -> str:
        nonlocal unresolved
        name = match.group("name")
        replacement = constants.get(name)
        if replacement is None:
            unresolved = True
            return ""
        return replacement

    resolved = _TEMPLATE_SLOT_RE.sub(replace, body)
    return None if unresolved or "${" in resolved else resolved


def _evaluate_expression(
    expression: str,
    *,
    constants: dict[str, str],
    importer: str,
) -> tuple[str, bool, bool] | None:
    value = expression.strip()
    if not value or len(value) > _MAX_EXPRESSION_CHARS:
        return None
    direct = _literal(value)
    if direct is not None:
        return direct, False, False
    template = _template_value(value, constants)
    if template is not None:
        return template, False, True
    if value in constants:
        return constants[value], False, True

    path_call = re.fullmatch(r"path\.(?:join|resolve)\((.*)\)", value)
    if path_call:
        args = _split_top_level(path_call.group(1), ",")
        if not args:
            return None
        pieces: list[str] = []
        rooted = False
        heuristic = True
        for arg in args:
            if arg == "__dirname":
                pieces.append(PurePosixPath(importer).parent.as_posix())
                rooted = True
                continue
            evaluated = _evaluate_expression(
                arg,
                constants=constants,
                importer=importer,
            )
            if evaluated is None:
                return None
            pieces.append(evaluated[0])
            rooted = rooted or evaluated[1]
            heuristic = heuristic or evaluated[2]
        return posixpath.join(*pieces), rooted, heuristic

    concat = _split_top_level(value, "+")
    if concat and len(concat) > 1:
        pieces = []
        rooted = False
        heuristic = True
        for part in concat:
            evaluated = _evaluate_expression(
                part,
                constants=constants,
                importer=importer,
            )
            if evaluated is None:
                return None
            pieces.append(evaluated[0])
            rooted = rooted or evaluated[1]
            heuristic = heuristic or evaluated[2]
        return "".join(pieces), rooted, heuristic
    return None


def _constants(text: str, importer: str) -> dict[str, str]:
    constants: dict[str, str] = {}
    pending = [
        (match.group("name"), match.group("expr")) for match in _CONST_RE.finditer(text)
    ]
    for _ in range(4):
        changed = False
        for name, expression in pending:
            if name in constants:
                continue
            evaluated = _evaluate_expression(
                expression,
                constants=constants,
                importer=importer,
            )
            if evaluated is not None:
                constants[name] = evaluated[0]
                changed = True
        if not changed:
            break
    return constants


def _references(text: str, importer: str) -> list[_Reference]:
    constants = _constants(text, importer)
    refs: list[_Reference] = []
    occupied: set[tuple[int, str]] = set()
    for match in _FROM_RE.finditer(text):
        kind: StaticArtifactReachabilityEdgeKind = (
            "import" if match.group("kind") == "import" else "export"
        )
        refs.append(
            _Reference(
                line_number=_line_number(text, match.start()),
                kind=kind,
                expression=match.group("spec"),
                specifier=match.group("spec"),
                confidence="literal",
            )
        )
        occupied.add((match.start(), match.group("spec")))
    for match in _SIDE_EFFECT_IMPORT_RE.finditer(text):
        key = (match.start(), match.group("spec"))
        if key in occupied:
            continue
        refs.append(
            _Reference(
                line_number=_line_number(text, match.start()),
                kind="import",
                expression=match.group("spec"),
                specifier=match.group("spec"),
                confidence="literal",
            )
        )
    for match in _CALL_RE.finditer(text):
        call = match.group("call")
        kind_map: dict[str, StaticArtifactReachabilityEdgeKind] = {
            "require": "require",
            "import": "dynamic_import",
            "require.resolve": "require_resolve",
        }
        expression = match.group("expr").strip()
        evaluated = _evaluate_expression(
            expression,
            constants=constants,
            importer=importer,
        )
        kind = kind_map[call]
        if "path.join" in expression or "path.resolve" in expression:
            kind = "path_loader"
        specifier = evaluated[0] if evaluated is not None else None
        if specifier and PurePosixPath(specifier).suffix.lower() in {".node", ".wasm"}:
            kind = "native_loader"
        refs.append(
            _Reference(
                line_number=_line_number(text, match.start()),
                kind=kind,
                expression=expression[:200],
                specifier=specifier,
                confidence="literal" if evaluated and not evaluated[2] else "heuristic",
                rooted=bool(evaluated and evaluated[1]),
            )
        )
    for match in _SOURCE_MAP_RE.finditer(text):
        specifier = match.group("spec")
        if not specifier.startswith((".", "/", "data:", "http:", "https:")):
            specifier = f"./{specifier}"
        refs.append(
            _Reference(
                line_number=_line_number(text, match.start()),
                kind="source_map",
                expression=match.group("spec")[:200],
                specifier=specifier,
                confidence="literal",
            )
        )
    return sorted(
        refs,
        key=lambda item: (
            item.line_number,
            item.kind,
            item.specifier or item.expression,
        ),
    )


def _candidate_paths(base: str) -> tuple[str, ...]:
    suffix = PurePosixPath(base).suffix.lower()
    candidates = [base]
    if suffix not in _LOADER_SUFFIXES:
        candidates.extend(f"{base}{item}" for item in _LOADER_SUFFIXES)
        candidates.extend(f"{base}/index{item}" for item in _LOADER_SUFFIXES)
    return tuple(dict.fromkeys(posixpath.normpath(item) for item in candidates))


def _package_parts(specifier: str) -> tuple[str, str]:
    parts = PurePosixPath(specifier).parts
    if not parts:
        return "", ""
    if parts[0].startswith("@") and len(parts) >= 2:
        return "/".join(parts[:2]), "/".join(parts[2:])
    return parts[0], "/".join(parts[1:])


def _package_entrypoint(
    package_root: str,
    *,
    paths: dict[str, tuple[Path, int]],
    limit_reasons: set[StaticReachabilityLimitReason],
) -> str:
    manifest_path = f"{package_root}/package.json"
    record = paths.get(manifest_path)
    if record is None:
        return "index"
    path, size = record
    if size > _MAX_PACKAGE_MANIFEST_BYTES:
        limit_reasons.add("parse_error")
        return "index"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        limit_reasons.add("read_error")
        return "index"
    except (UnicodeDecodeError, json.JSONDecodeError):
        limit_reasons.add("parse_error")
        return "index"
    if not isinstance(payload, dict):
        limit_reasons.add("parse_error")
        return "index"
    for field in ("browser", "main"):
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value.lstrip("./")
    return "index"


def _resolve(
    reference: _Reference,
    *,
    importer: str,
    available: set[str],
    paths: dict[str, tuple[Path, int]],
    limit_reasons: set[StaticReachabilityLimitReason],
) -> str | None:
    specifier = reference.specifier
    if not specifier or specifier.startswith(("data:", "http:", "https:")):
        return None
    if specifier.startswith("node:") or specifier.split("/", 1)[0] in _BUILTIN_MODULES:
        return "<external>"
    if reference.rooted:
        base = posixpath.normpath(specifier)
    elif specifier.startswith("."):
        base = posixpath.normpath(
            posixpath.join(PurePosixPath(importer).parent.as_posix(), specifier)
        )
    elif specifier.startswith("/"):
        return None
    else:
        package, subpath = _package_parts(specifier)
        if not package:
            return None
        parents = [PurePosixPath(importer).parent, *PurePosixPath(importer).parents]
        roots = [
            (parent / "node_modules" / package).as_posix()
            for parent in parents
            if parent.as_posix() not in {"", "."}
        ]
        roots.append(f"node_modules/{package}")
        package_root = next(
            (
                root
                for root in dict.fromkeys(roots)
                if any(
                    path == root or path.startswith(f"{root}/") for path in available
                )
            ),
            None,
        )
        if package_root is None:
            return None
        entry = subpath or _package_entrypoint(
            package_root,
            paths=paths,
            limit_reasons=limit_reasons,
        )
        base = posixpath.join(package_root, entry)
    if base == ".." or base.startswith("../"):
        return None
    return next((item for item in _candidate_paths(base) if item in available), None)


def build_reachability_graph(
    context: StaticAnalysisContext,
    *,
    max_file_bytes: int,
) -> ReachabilityGraphResult:
    """Build a bounded BFS graph rooted at resolved manifest entrypoints."""

    records = {
        relative_path: (path, size)
        for relative_path, path, size in context.iter_file_records()
    }
    available = set(records)
    roots = tuple(path for path in context.resolved_entrypoints() if path in available)
    manifest_parent = context.manifest_relative_path or "package.json"
    provenance = {
        root: ReachabilityProvenance(
            depth=0,
            parent=manifest_parent,
            edge_kind="manifest",
            confidence="literal",
        )
        for root in roots
    }
    queue = deque(sorted(roots))
    edges: set[tuple[str, str, str]] = set()
    unresolved: list[StaticReachabilityUnresolvedReference] = []
    unresolved_count = 0
    bytes_read = 0
    limit_reasons: set[StaticReachabilityLimitReason] = set()

    while queue:
        importer = queue.popleft()
        node = provenance[importer]
        record = records.get(importer)
        if (
            record is None
            or PurePosixPath(importer).suffix.lower() not in _TRAVERSABLE_SUFFIXES
        ):
            continue
        path, size = record
        if size > max_file_bytes:
            limit_reasons.add("parse_error")
            continue
        if bytes_read + size > MAX_REACHABILITY_BYTES:
            limit_reasons.add("byte_cap")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            limit_reasons.add("read_error")
            continue
        except UnicodeDecodeError:
            limit_reasons.add("parse_error")
            continue
        bytes_read += size
        for reference in _references(text, importer):
            target = _resolve(
                reference,
                importer=importer,
                available=available,
                paths=records,
                limit_reasons=limit_reasons,
            )
            if target == "<external>":
                continue
            if target is None:
                unresolved_count += 1
                if len(unresolved) < MAX_UNRESOLVED_DETAILS:
                    unresolved.append(
                        StaticReachabilityUnresolvedReference(
                            source_path=importer,
                            line_number=reference.line_number,
                            edge_kind=reference.kind,
                            expression=(reference.expression or "<computed>")[:200],
                        )
                    )
                continue
            edge = (importer, target, reference.kind)
            if edge in edges:
                continue
            if len(edges) >= MAX_REACHABILITY_EDGES:
                limit_reasons.add("edge_cap")
                break
            edges.add(edge)
            if target in provenance:
                continue
            depth = node.depth + 1
            if depth > MAX_REACHABILITY_DEPTH:
                limit_reasons.add("depth_cap")
                continue
            if len(provenance) >= MAX_REACHABILITY_NODES:
                limit_reasons.add("node_cap")
                continue
            provenance[target] = ReachabilityProvenance(
                depth=depth,
                parent=importer,
                edge_kind=reference.kind,
                confidence=reference.confidence,
            )
            queue.append(target)

    reason_map: dict[StaticReachabilityLimitReason, StaticCoverageReason] = {
        "node_cap": "reachability_node_cap",
        "edge_cap": "reachability_edge_cap",
        "byte_cap": "reachability_byte_cap",
        "depth_cap": "reachability_depth_cap",
        "read_error": "reachability_read_error",
        "parse_error": "reachability_parse_error",
    }
    return ReachabilityGraphResult(
        provenance=provenance,
        summary=StaticReachabilitySummary(
            roots=list(roots),
            nodes_reached=len(provenance),
            edges_resolved=len(edges),
            bytes_read=bytes_read,
            unresolved_count=unresolved_count,
            unresolved_references=sorted(
                unresolved,
                key=lambda item: (
                    item.source_path,
                    item.line_number,
                    item.edge_kind,
                    item.expression,
                ),
            ),
            limit_reasons=sorted(limit_reasons),
        ),
        coverage_reasons=tuple(sorted(reason_map[reason] for reason in limit_reasons)),
    )


__all__ = [
    "MAX_REACHABILITY_BYTES",
    "MAX_REACHABILITY_DEPTH",
    "MAX_REACHABILITY_EDGES",
    "MAX_REACHABILITY_NODES",
    "ReachabilityGraphResult",
    "ReachabilityProvenance",
    "build_reachability_graph",
]
