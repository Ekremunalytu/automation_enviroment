const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const path = require("node:path");

const { CONTEXT_PATH, HARNESS_RUN_COMMAND_ID, READY_PATH } = require("./constants");

// W13-1 (Codex H6): in-memory copy of the per-launch HMAC secret. Set
// by extension.js::activate() after reading and unlinking
// HARNESS_SECRET_PATH; never re-read from disk. If the read fails the
// value stays empty and emit functions skip signing — Python-side
// reconciliation will reject unsigned markers (fail-closed).
let _harnessNonceSecret = "";

function setHarnessNonceSecret(secret) {
  _harnessNonceSecret = typeof secret === "string" ? secret : "";
}

// Output channel reference for marker emission. ``console.log`` cannot be
// used because launch_vscode.sh redirects VS Code stdout/stderr to
// /dev/null, so Extension Host console output never reaches the parser.
// extension.js::activate() installs the channel via setHarnessChannel
// after createOutputChannel; until then emitters fall back to console.log
// (preserved for tests / dev mode that read Developer Tools console).
let _harnessChannel = null;

function setHarnessChannel(channel) {
  _harnessChannel = channel && typeof channel.appendLine === "function" ? channel : null;
}

function _emitMarkerLine(line) {
  if (_harnessChannel) {
    _harnessChannel.appendLine(line);
    return;
  }
  console.log(line);
}

// HMAC input shape mirrors tests/executor/test_playwright_health_reconciliation.py
// _w13_1_canonical_payload: sorted-keys JSON without whitespace, the
// ``nonce`` key itself excluded so the signature covers the unsigned
// envelope. Keep this in lockstep with the Python verifier (sub-commit 4).
function _canonicalPayloadBytes(payload) {
  const filtered = {};
  for (const key of Object.keys(payload).sort()) {
    if (key === "nonce") continue;
    filtered[key] = payload[key];
  }
  return JSON.stringify(filtered);
}

function _signedPayload(payload) {
  if (!_harnessNonceSecret) {
    return payload;
  }
  const signature = crypto
    .createHmac("sha256", _harnessNonceSecret)
    .update(_canonicalPayloadBytes(payload))
    .digest("hex");
  return { ...payload, nonce: signature };
}

async function readHarnessContext() {
  try {
    const raw = await fs.readFile(CONTEXT_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function emitHarnessMarker(phase, details) {
  _emitMarkerLine(
    `[extrace-harness] ${JSON.stringify(
      _signedPayload({
        kind: "stimulus",
        phase,
        ...details,
      })
    )}`
  );
}

// PR345 PR5: generic JSON-line emitter for non-stimulus harness events
// (e.g. output_channel_appendline). Caller supplies the full payload —
// in particular the ``kind`` field. Reuses the [extrace-harness] prefix
// the existing _HARNESS_MARKER_RE consumes on the Python side.
function emitHarnessEvent(payload) {
  _emitMarkerLine(`[extrace-harness] ${JSON.stringify(_signedPayload(payload))}`);
}

// W8-0: marker payload schema version. Bumped only when the contract
// the Python parser depends on (parse_harness_ready_marker) changes
// in a non-additive way. Additive fields do not require a bump.
const HARNESS_MARKER_VERSION = 1;

async function writeHarnessReadyMarker() {
  await fs.mkdir(path.dirname(READY_PATH), { recursive: true });
  const payload = {
    ready_at_unix: Date.now() / 1000,
    command: HARNESS_RUN_COMMAND_ID,
    marker_version: HARNESS_MARKER_VERSION,
    epoch_run_id: process.env.EXTRACE_EPOCH_RUN_ID || "",
    pid: process.pid,
  };
  // Atomic write: tmp + rename. POSIX rename within the same fs is
  // atomic, so a Python reader can never observe a half-written marker.
  const tmpPath = `${READY_PATH}.tmp-${process.pid}`;
  await fs.writeFile(tmpPath, JSON.stringify(payload), "utf8");
  await fs.rename(tmpPath, READY_PATH);
}

module.exports = {
  emitHarnessEvent,
  emitHarnessMarker,
  readHarnessContext,
  setHarnessChannel,
  setHarnessNonceSecret,
  writeHarnessReadyMarker,
};
