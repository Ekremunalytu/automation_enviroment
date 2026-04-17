const fs = require("node:fs/promises");

const { CONTEXT_PATH } = require("./constants");

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

module.exports = {
  emitHarnessMarker,
  readHarnessContext,
};
