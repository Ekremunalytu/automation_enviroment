"""Fire / silent / FP-guard unit tests for the S15 path-traversal-server rule.

Inputs are SYNTHETIC — hand-authored ~20-line reproductions of the *shape* of the
Snyk-labs Instant Markdown vulnerability class (a local static HTTP server that
maps a request path onto an unguarded ``fs.readFile`` and exposes it cross-origin).
The real vulnerable extension is **never** downloaded into the repo; only the
declawed pattern is reproduced (see the detection-design README safety section).
No exploit page, no ``track.php`` receiver, no live host — those are out of scope
(spec §0/§7).
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s15_path_traversal_server import PathTraversalServerRule

MakeContext = Callable[..., StaticAnalysisContext]

# Positive fixture: the vulnerable shape. Local HTTP server, request path fed
# straight into fs.readFile with NO containment guard, permissive CORS so a
# browser page can reach it. This is the Instant Markdown 1.4.6 class, declawed.
_VULN_CORS = """
const http = require("http");
const fs = require("fs");
const ROOT = process.cwd();

const server = http.createServer((req, res) => {
  // request path mapped straight onto the filesystem — no traversal guard
  const filePath = ROOT + req.url;
  res.setHeader("Access-Control-Allow-Origin", "*");
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200);
    res.end(data);
  });
});
server.listen(8090);
"""

# Positive fixture: the webview reachable-origin variant (VLN3) — untrusted
# render with scripts enabled and no CSP, same unguarded request->read flow.
_VULN_WEBVIEW = """
const http = require("http");
const fs = require("fs");
function preview(panel, root) {
  panel.webview.options = { enableScripts: true };
  panel.webview.html = "<html><body>" + userMarkdownAsHtml + "</body></html>";
  const app = require("http").createServer((req, res) => {
    const p = root + req.url;
    fs.createReadStream(p).pipe(res);
  });
  app.listen(0);
}
"""

# Negative fixture: the SAME server, correctly guarded with path.resolve +
# startsWith(root) containment. The primitive is closed — must stay silent.
_SAFE_GUARDED = """
const http = require("http");
const fs = require("fs");
const path = require("path");
const ROOT = process.cwd();

const server = http.createServer((req, res) => {
  const resolved = path.resolve(ROOT, "." + req.url);
  if (!resolved.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  res.setHeader("Access-Control-Allow-Origin", "*");
  fs.readFile(resolved, (err, data) => res.end(data));
});
server.listen(8090);
"""


def test_fires_on_unguarded_server_with_permissive_cors(
    make_context: MakeContext,
) -> None:
    ctx = make_context(files={"server.js": _VULN_CORS})
    findings = PathTraversalServerRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s15.path_traversal_server"
    # Vulnerability surface, not malice — MEDIUM/WARN, never CRITICAL/BLOCK.
    assert finding.severity.value == "medium"
    assert finding.confidence.value == "medium"
    assert finding.adversary_class is None
    assert "extrace.ext.path_traversal_server" in finding.categories
    assert finding.evidence  # server + sink + reachable-origin lines cited


def test_fires_on_webview_no_csp_variant(make_context: MakeContext) -> None:
    # The VLN3 reachable-origin path: scripted webview, no CSP meta tag.
    ctx = make_context(files={"preview.js": _VULN_WEBVIEW})
    assert len(PathTraversalServerRule().evaluate(ctx)) == 1


def test_silent_when_path_resolve_startswith_guard_present(
    make_context: MakeContext,
) -> None:
    # The load-bearing FP guard: a correctly-contained server (resolve +
    # startsWith(root)) is benign and correct — flagging it destroys trust.
    ctx = make_context(files={"server.js": _SAFE_GUARDED})
    assert PathTraversalServerRule().evaluate(ctx) == []


def test_silent_when_served_through_hardened_static_lib(
    make_context: MakeContext,
) -> None:
    # serve-static / send do root-containment internally — treat as guarded.
    src = (
        'const express = require("express");\n'
        'const serveStatic = require("serve-static");\n'
        "const app = express();\n"
        "app.use(serveStatic(root));\n"
        'app.get("/f", (req, res) => res.sendFile(root + req.url));\n'
        "app.listen(8090);\n"
    )
    ctx = make_context(files={"server.js": src})
    assert PathTraversalServerRule().evaluate(ctx) == []


def test_silent_for_local_server_without_fs_read(make_context: MakeContext) -> None:
    # A dev-server / LSP-over-http that never reads files off a request path —
    # VLN1 alone is wildly benign and must not fire.
    src = (
        'const http = require("http");\n'
        "const server = http.createServer((req, res) => {\n"
        '  res.setHeader("Access-Control-Allow-Origin", "*");\n'
        "  res.end(JSON.stringify({ ok: true }));\n"
        "});\n"
        "server.listen(3000);\n"
    )
    ctx = make_context(files={"server.js": src})
    assert PathTraversalServerRule().evaluate(ctx) == []


def test_silent_for_unguarded_read_but_no_reachable_origin(
    make_context: MakeContext,
) -> None:
    # Server + unguarded request->read, but locked to a same-origin caller (no
    # permissive CORS, no webview). The reachable-origin conjunct is missing, so
    # the browser-driven exploit path does not exist — stay silent.
    src = (
        'const http = require("http");\n'
        'const fs = require("fs");\n'
        "const server = http.createServer((req, res) => {\n"
        "  fs.readFile(root + req.url, (e, d) => res.end(d));\n"
        "});\n"
        "server.listen(8090);\n"
    )
    ctx = make_context(files={"server.js": src})
    assert PathTraversalServerRule().evaluate(ctx) == []


def test_silent_for_fs_read_without_local_server(make_context: MakeContext) -> None:
    # An extension that reads a config file on a request-shaped variable but
    # stands up no server at all — VLN1 missing, no primitive.
    src = (
        'const fs = require("fs");\n'
        "function load(req) { return fs.readFileSync(base + req.url); }\n"
    )
    ctx = make_context(files={"util.js": src})
    assert PathTraversalServerRule().evaluate(ctx) == []


def test_silent_when_bundle_conjuncts_are_in_unrelated_regions(
    make_context: MakeContext,
) -> None:
    padding = "const bundledData = '" + ("x" * 9000) + "';"
    src = (
        'http.createServer(handler); res.setHeader("Access-Control-Allow-Origin", "*");'
        + padding
        + "function unrelated(req) { return fs.readFileSync(root + req.url); }"
    )
    ctx = make_context(files={"bundle.js": src})
    assert PathTraversalServerRule().evaluate(ctx) == []
