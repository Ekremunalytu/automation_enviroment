const fs = require("node:fs/promises");
const path = require("node:path");

const { CONTEXT_PATH, HARNESS_RUN_COMMAND_ID, READY_PATH } = require("./constants");

async function readHarnessContext() {
  try {
    const raw = await fs.readFile(CONTEXT_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function emitHarnessMarker(phase, details) {
  console.log(
    `[extrace-harness] ${JSON.stringify({
      kind: "stimulus",
      phase,
      ...details,
    })}`
  );
}

// PR345 PR5: generic JSON-line emitter for non-stimulus harness events
// (e.g. output_channel_appendline). Caller supplies the full payload —
// in particular the ``kind`` field. Reuses the [extrace-harness] prefix
// the existing _HARNESS_MARKER_RE consumes on the Python side.
function emitHarnessEvent(payload) {
  console.log(`[extrace-harness] ${JSON.stringify(payload)}`);
}

async function writeHarnessReadyMarker() {
  await fs.mkdir(path.dirname(READY_PATH), { recursive: true });
  const payload = {
    ready_at_unix: Date.now() / 1000,
    command: HARNESS_RUN_COMMAND_ID,
  };
  await fs.writeFile(READY_PATH, JSON.stringify(payload), "utf8");
}

module.exports = {
  emitHarnessEvent,
  emitHarnessMarker,
  readHarnessContext,
  writeHarnessReadyMarker,
};
